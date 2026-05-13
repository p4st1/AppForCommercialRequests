import ast
import decimal
import hashlib
import json
import os
import re
import shutil
import sys
import time
import traceback
from pathlib import Path
from config import Config

class DatabaseTools:
    def __init__(self):
        pass

    @staticmethod
    def phoneNumToStr(num):
        num = str(num)
        return f'+{num[0]} ({num[1:4]}) {num[4:7]}-{num[7:9]}-{num[9:]}'

    @staticmethod
    def _safe_eval(expression: str) -> float:
        allowed_binary = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.Pow: lambda a, b: a ** b,
        }
        allowed_unary = {
            ast.UAdd: lambda a: a,
            ast.USub: lambda a: -a,
        }
        ast_num = getattr(ast, "Num", None)

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return float(node.value)
            if ast_num is not None and isinstance(node, ast_num):
                return float(node.n)
            if isinstance(node, ast.BinOp) and type(node.op) in allowed_binary:
                return allowed_binary[type(node.op)](_eval(node.left), _eval(node.right))
            if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_unary:
                return allowed_unary[type(node.op)](_eval(node.operand))
            if isinstance(node, ast.Call):
                raise ValueError("Функции в формулах не поддерживаются")
            raise ValueError("Недопустимое выражение")

        parsed = ast.parse(expression, mode="eval")
        return float(_eval(parsed))

    @staticmethod
    def _to_bool(value, default=False):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "y", "on"}:
                return True
            if normalized in {"false", "0", "no", "n", "off"}:
                return False
        return default

    @staticmethod
    def _coerce_setting_value(value, default):
        if isinstance(default, bool):
            return DatabaseTools._to_bool(value, default)

        if isinstance(default, int):
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                text = value.strip().replace(",", ".")
                if not text:
                    return default
                try:
                    return int(float(text))
                except ValueError:
                    return default
            return default

        if isinstance(default, float):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
            if isinstance(value, str):
                text = value.strip().replace(",", ".")
                if not text:
                    return default
                try:
                    return float(text)
                except ValueError:
                    return default
            return default

        if isinstance(default, str):
            if value is None:
                return default
            return str(value)

        return value if value is not None else default

    @staticmethod
    def _normalize_cookies_dict(raw_value) -> dict[str, str]:
        if not isinstance(raw_value, dict):
            return {}
        normalized: dict[str, str] = {}
        for key, value in raw_value.items():
            key_text = str(key).strip()
            value_text = str(value).strip()
            if not key_text or not value_text:
                continue
            normalized[key_text] = value_text
        return normalized

    @staticmethod
    def merge_config_with_defaults(raw_data: dict | None) -> dict:
        data = raw_data if isinstance(raw_data, dict) else {}
        raw_config = data.get("config", {})
        raw_settings = data.get("settings", {})
        raw_root_cookies = data.get("cookies")

        config = Config.DEFAULT_CONFIG.copy()
        if isinstance(raw_config, dict):
            config.update(raw_config)

        cookies_from_config = DatabaseTools._normalize_cookies_dict(config.get("cookies"))
        cookies_from_root = DatabaseTools._normalize_cookies_dict(raw_root_cookies)
        normalized_cookies = cookies_from_config or cookies_from_root
        if normalized_cookies:
            config["cookies"] = normalized_cookies

        # Backward compatibility for older key name.
        if "customLine" in config and "customNum" not in raw_config:
            config["customNum"] = str(config["customLine"])

        if not str(config.get("pathToSaveExcel", "")).strip():
            config["pathToSaveExcel"] = str(config.get("pathToSaveCP", "")).strip()

        config["logisticVar"] = str(config.get("logisticVar", "0"))
        config["logisticNum"] = str(config.get("logisticNum", "1"))
        config["customNum"] = str(config.get("customNum", "1"))
        config["termDelivery"] = str(config.get("termDelivery", "0"))
        config["markup"] = str(config.get("markup", "1"))
        config["requestNumber"] = str(config.get("requestNumber", "")).strip()
        config["ExcelIndent"] = str(config.get("ExcelIndent", "0"))
        config["lastTable"] = str(config.get("lastTable", "")).strip()
        config["pathToSaveCP"] = str(config.get("pathToSaveCP", "")).strip()
        config["pathToSaveExcel"] = str(config.get("pathToSaveExcel", "")).strip()
        config["offerValidityDays"] = str(
            Config.normalize_offer_validity_days(config.get("offerValidityDays"))
        )
        if not isinstance(config.get("lastCreateDocFields"), dict):
            config["lastCreateDocFields"] = {}

        payment_templates_raw = config.get("paymentTemplates")
        if isinstance(payment_templates_raw, str):
            payment_templates_values = [payment_templates_raw]
        elif isinstance(payment_templates_raw, (list, tuple)):
            payment_templates_values = list(payment_templates_raw)
        else:
            payment_templates_values = []

        normalized_payment_templates = []
        for template in payment_templates_values:
            text = str(template or "").strip()
            if not text or text in normalized_payment_templates:
                continue
            normalized_payment_templates.append(text)

        if not normalized_payment_templates and (
            not isinstance(raw_config, dict) or "paymentTemplates" not in raw_config
        ):
            normalized_payment_templates = Config.DEFAULT_PAYMENT_TEMPLATES.copy()

        config["paymentTemplates"] = normalized_payment_templates

        settings = Config.DEFAULT_SETTINGS.copy()
        if isinstance(raw_settings, dict):
            for key, default_value in settings.items():
                settings[key] = DatabaseTools._coerce_setting_value(
                    raw_settings.get(key),
                    default_value,
                )

        result = {"config": config, "settings": settings}
        if normalized_cookies:
            result["cookies"] = normalized_cookies
        return result

    @staticmethod
    def evalWithVars(line):
        expression = str(line or "").strip().replace(",", ".")
        if not expression:
            raise ValueError("Пустая формула")

        paramsData = DatabaseTools.load_json(Config.vars_path)
        parameters = {}
        for values in paramsData.get("parameters", {}).values():
            if len(values) >= 3:
                variable, value, calc = values[0], values[1], values[2]
                parameters[str(variable)] = (str(value), str(calc))

        def replace_var(match):
            token = match.group(1).strip()
            if token not in parameters:
                raise ValueError(f"Неизвестная переменная: {token}")
            value, calc = parameters[token]
            if calc == "percents":
                return f"({value})/100"
            if calc == "multiply":
                return f"*({value})"
            if calc == "division":
                return f"/({value})"
            return f"({value})"

        expression = re.sub(r"\$([^$]+)\$", replace_var, expression)
        expression = expression.strip()
        while expression and expression[0] in "+*/":
            expression = expression[1:]

        if not expression:
            raise ValueError("Пустая формула")

        return round(DatabaseTools._safe_eval(expression), 4)

    @staticmethod
    def resourcePath(relativePath):
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        return os.path.join(base_path, relativePath)

    @staticmethod
    def getCalc(value):
        if value == "percents":
            return "%"
        if value == 'multiply':
            return '*'
        if value == 'division':
            return '/'

    @staticmethod
    def validNum(value):
        normalized = DatabaseTools._normalize_number_text(value, prefer_thousands=False)
        if not normalized:
            return None
        try:
            float(normalized)
        except ValueError:
            return None
        else:
            return float(normalized)

    @staticmethod
    def _normalize_number_text(value, *, prefer_thousands=True) -> str:
        text = str(value or "").strip().replace("\u00A0", "").replace(" ", "")
        if not text:
            return ""

        sign = ""
        if text[0] in "+-":
            sign = text[0]
            text = text[1:]
        if not text:
            return sign

        if "," in text and "." in text:
            # If both separators are present, the rightmost one is decimal,
            # the other is used as thousands separator.
            last_comma = text.rfind(",")
            last_dot = text.rfind(".")
            decimal_sep = "," if last_comma > last_dot else "."
            thousands_sep = "." if decimal_sep == "," else ","
            text = text.replace(thousands_sep, "")
            if decimal_sep == ",":
                text = text.replace(",", ".")
            return sign + text

        sep = "," if "," in text else "." if "." in text else ""
        if not sep:
            return sign + text

        parts = text.split(sep)
        if len(parts) > 2:
            if all(part.isdigit() for part in parts) and all(len(part) == 3 for part in parts[1:]):
                return sign + "".join(parts)
            integer_part = "".join(parts[:-1])
            fraction_part = parts[-1]
            if integer_part.isdigit() and fraction_part.isdigit():
                return sign + f"{integer_part}.{fraction_part}"
            if sep == ",":
                return sign + text.replace(",", ".")
            return sign + text

        left, right = parts
        if left.isdigit() and right.isdigit():
            if len(right) == 3 and prefer_thousands:
                return sign + left + right
            return sign + f"{left}.{right}"

        if sep == ",":
            return sign + text.replace(",", ".")
        return sign + text

    @staticmethod
    def parse_int(value, field_name: str, allow_zero=True) -> int:
        normalized = DatabaseTools._normalize_number_text(value, prefer_thousands=True)
        if not normalized:
            raise ValueError(f'Поле "{field_name}" не заполнено')
        try:
            parsed = float(normalized)
        except ValueError:
            raise ValueError(f'Поле "{field_name}" должно быть числом')
        if not parsed.is_integer():
            raise ValueError(f'Поле "{field_name}" должно быть целым числом')
        parsed_int = int(parsed)
        if parsed_int < 0 or (parsed_int == 0 and not allow_zero):
            relation = "положительным" if not allow_zero else "неотрицательным"
            raise ValueError(f'Поле "{field_name}" должно быть {relation} числом')
        return parsed_int

    @staticmethod
    def parse_float(value, field_name: str, allow_zero=True) -> float:
        normalized = DatabaseTools._normalize_number_text(value, prefer_thousands=False)
        if not normalized:
            raise ValueError(f'Поле "{field_name}" не заполнено')
        try:
            parsed = float(normalized)
        except ValueError:
            raise ValueError(f'Поле "{field_name}" должно быть числом')
        if parsed < 0 or (parsed == 0 and not allow_zero):
            relation = "положительным" if not allow_zero else "неотрицательным"
            raise ValueError(f'Поле "{field_name}" должно быть {relation} числом')
        return parsed

    @staticmethod
    def parse_delivery_days(value) -> int:
        text = str(value or "").strip()
        if not text:
            return 0
        match = re.search(r"(-?\d+)", text)
        if not match:
            raise ValueError(f'Не удалось распознать срок поставки: "{text}"')
        days = int(match.group(1))
        if days < 0:
            raise ValueError(f'Срок поставки не может быть отрицательным: "{text}"')
        return days

    @staticmethod
    def _preferred_user_data_dir(app_name: str) -> Path:
        if sys.platform.startswith("win"):
            return Path(os.environ["APPDATA"]) / app_name
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / app_name
        return Path.home() / ".local" / "share" / app_name

    @staticmethod
    def user_data_dir(app_name: str) -> Path:
        preferred = DatabaseTools._preferred_user_data_dir(app_name)
        fallback = Path.cwd() / ".appdata" / app_name
        for candidate in (preferred, fallback):
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                probe = candidate / ".write_probe"
                with open(probe, "w", encoding="utf-8") as f:
                    f.write("ok")
                probe.unlink(missing_ok=True)
                return candidate
            except Exception as e:
                DatabaseTools.log_exception(
                    f"Не удалось создать директорию данных: {candidate}",
                    e,
                    include_traceback=False,
                )
                continue

        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    @staticmethod
    def _source_versions_path(app_name: str) -> Path:
        return DatabaseTools.user_data_dir(app_name) / ".bundle_versions.json"

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as file:
            while True:
                chunk = file.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _load_source_versions(app_name: str) -> dict:
        versions_path = DatabaseTools._source_versions_path(app_name)
        try:
            data = DatabaseTools.load_json(versions_path)
        except Exception as e:
            DatabaseTools.log_exception(
                f"Не удалось загрузить версии ресурсов: {versions_path}",
                e,
                include_traceback=False,
            )
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _save_source_versions(app_name: str, versions: dict) -> None:
        versions_path = DatabaseTools._source_versions_path(app_name)
        DatabaseTools.save_json_atomic(versions_path, versions)

    @staticmethod
    def _merge_json_defaults(current_value, default_value):
        if isinstance(default_value, dict):
            if not isinstance(current_value, dict):
                current_value = {}
            merged = dict(current_value)
            for key, value in default_value.items():
                merged[key] = DatabaseTools._merge_json_defaults(current_value.get(key), value)
            return merged

        if current_value is None:
            return default_value
        return current_value

    @staticmethod
    def _sync_json_with_defaults(dst: Path, src: Path) -> None:
        try:
            source_data = DatabaseTools.load_json(src)
        except Exception as e:
            DatabaseTools.log_exception(
                f"Не удалось прочитать исходный JSON {src}, выполняется копирование",
                e,
                include_traceback=False,
            )
            shutil.copy2(src, dst)
            return

        try:
            current_data = DatabaseTools.load_json(dst)
        except Exception as e:
            DatabaseTools.log_exception(
                f"Не удалось прочитать пользовательский JSON {dst}, применяются значения по умолчанию",
                e,
                include_traceback=False,
            )
            current_data = {}

        merged = DatabaseTools._merge_json_defaults(current_data, source_data)
        DatabaseTools.save_json_atomic(dst, merged)

    @staticmethod
    def ensure_user_file(
        app_name: str,
        template_rel_path: str,
        target_name: str,
        f=0,
        sync_mode: str = "if_missing",
    ) -> Path:
        dst_dir = DatabaseTools.user_data_dir(app_name)
        dst_dir.mkdir(parents=True, exist_ok=True)

        dst = dst_dir / target_name
        src = Path(DatabaseTools.resourcePath(template_rel_path))
        legacy = DatabaseTools._preferred_user_data_dir(app_name) / target_name

        if not dst.exists():
            copied = False
            if legacy.exists() and legacy != dst:
                try:
                    shutil.copy2(legacy, dst)
                    copied = True
                except Exception as e:
                    DatabaseTools.log_exception(
                        f"Не удалось скопировать legacy-файл {legacy} -> {dst}",
                        e,
                        include_traceback=False,
                    )
                    copied = False
            if not copied:
                shutil.copy2(src, dst)

        if f:
            shutil.copy2(src, dst)
            return dst

        if sync_mode == "if_missing":
            return dst

        versions = DatabaseTools._load_source_versions(app_name)
        current_source_hash = DatabaseTools._file_sha256(src)
        previous_source_hash = versions.get(target_name)

        if previous_source_hash != current_source_hash:
            if sync_mode == "replace_on_source_change":
                shutil.copy2(src, dst)
            elif sync_mode == "merge_json_on_source_change":
                DatabaseTools._sync_json_with_defaults(dst, src)
            versions[target_name] = current_source_hash
            DatabaseTools._save_source_versions(app_name, versions)

        elif target_name not in versions:
            versions[target_name] = current_source_hash
            DatabaseTools._save_source_versions(app_name, versions)

        return dst

    @staticmethod
    def load_json(path: Path) -> dict:
        file_path = Path(path)
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_json_atomic(path: Path, data: dict) -> None:
        file_path = Path(path)
        tmp = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(file_path)

    @staticmethod
    def _resolve_log_path(log_path: str | Path | None = None) -> Path:
        if log_path is not None:
            target = Path(log_path)
        else:
            configured = str(getattr(Config, "log_path", "") or "").strip()
            target = Path(configured) if configured else Path.cwd() / "logs.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    @staticmethod
    def write_log(message, log_path: str | Path | None = None):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_file = DatabaseTools._resolve_log_path(log_path)
        line = f"[{timestamp}] {message}\n"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            sys.stderr.write(line)

    @staticmethod
    def log_exception(
        context: str,
        error: Exception,
        *,
        include_traceback: bool = True,
        log_path: str | Path | None = None,
    ) -> None:
        DatabaseTools.write_log(
            f"[ERROR] {context}: {type(error).__name__}: {error}",
            log_path=log_path,
        )
        if include_traceback:
            tb = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            ).strip()
            if tb:
                for line in tb.splitlines():
                    DatabaseTools.write_log(line, log_path=log_path)

    @staticmethod
    def ensure_directory(path_value: str | Path | None, fallback_dir: Path) -> Path:
        raw = str(path_value or "").strip()
        windows_abs = bool(re.match(r"^[A-Za-z]:[\\/]", raw))
        if windows_abs and os.name != "nt":
            path = fallback_dir
        else:
            path = Path(raw).expanduser() if raw else fallback_dir
        if not path.is_absolute():
            path = (fallback_dir / path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def num2text(num):
        normalized = str(num).replace(" ", "").replace(",", ".")
        if "." not in normalized:
            normalized = f"{normalized}.00"
        num, mantissa = normalized.split('.', 1)
        if len(mantissa) < 2:
            mantissa = mantissa.ljust(2, "0")
        num = num[::-1]
        num = [num[i : i + 3] for i in range(0, len(num), 3)]
        res = ''
        for i in num[::-1]:
            res += f'{i[::-1]} '
        return f'{res.strip()},{mantissa}'

    @staticmethod
    def parsePrice(line):
        currency_ind = 0
        line = str(line or "").strip()
        for symb in Config.currencySymb:
            if symb in line:
                currency_ind = line.find(symb)
                break
        else:
            if "€" in line:
                currency_ind = line.find("€")
                symb = "€"
            else:
                return "", line
        if currency_ind == 0:
            return symb, line[1:].strip()
        return symb, line.replace(symb, "").strip()

    @staticmethod
    def formatPrice(price, currency):
        price_text = DatabaseTools.num2text(str(price).replace(" ", "").replace(",", "."))
        if not currency:
            return price_text
        if currency == '₽':
            return price_text + currency
        if currency in ['$', '¥', '€']:
            return currency + price_text
        return price_text

    @staticmethod
    def formWord(word, form):
        Dictionary = {
        'ор': ('ор', 'ора', 'ору', 'ора'),
        'ер': ('ер', 'ера', 'еру', 'ера'),
        'ль': ('ль', 'ля', 'лю', 'ля'),
        'нт': ('нт', 'нта', 'нту', 'нта'),
        'ат': ('ат', 'ата', 'ату', 'ата'),
        'ов': ('ов', 'ова', 'ову', 'ова'),
        'ев': ('ев', 'ева', 'еву', 'ева'),
        'ко': ('ко', 'ко', 'ко', 'ко'),
        'ов': ('ов', 'ова', 'ову', 'ова'),
        'ва': ('ва', 'вой', 'вой', 'ву'),
        'ик': ('ик', 'ика', 'ику', 'ика')
        }

        if len(word) < 2:
            return -1

        if word[-2:] not in Dictionary:
            return word

        return word[:-2] + Dictionary[word[-2:]][form]


class Tools:
    def __init__(self):
        self.units = (
            u'ноль',

            (u'один', u'одна'),
            (u'два', u'две'),

            u'три', u'четыре', u'пять',
            u'шесть', u'семь', u'восемь', u'девять'
        )

        self.teens = (
            u'десять', u'одиннадцать',
            u'двенадцать', u'тринадцать',
            u'четырнадцать', u'пятнадцать',
            u'шестнадцать', u'семнадцать',
            u'восемнадцать', u'девятнадцать'
        )

        self.tens = (
            self.teens,
            u'двадцать', u'тридцать',
            u'сорок', u'пятьдесят',
            u'шестьдесят', u'семьдесят',
            u'восемьдесят', u'девяносто'
        )

        self.hundreds = (
            u'сто', u'двести',
            u'триста', u'четыреста',
            u'пятьсот', u'шестьсот',
            u'семьсот', u'восемьсот',
            u'девятьсот'
        )

        self.orders = (# plural forms and gender
            #((u'', u'', u''), 'm'), # ((u'рубль', u'рубля', u'рублей'), 'm'), # ((u'копейка', u'копейки', u'копеек'), 'f')
            ((u'тысяча', u'тысячи', u'тысяч'), 'f'),
            ((u'миллион', u'миллиона', u'миллионов'), 'm'),
            ((u'миллиард', u'миллиарда', u'миллиардов'), 'm'),
        )

        self.minus = u'минус'


    def thousand(self, rest, sex):
        """Converts numbers from 19 to 999"""
        prev = 0
        plural = 2
        name = []
        use_teens = rest % 100 >= 10 and rest % 100 <= 19
        if not use_teens:
            data = ((self.units, 10), (self.tens, 100), (self.hundreds, 1000))
        else:
            data = ((self.teens, 10), (self.hundreds, 1000))
        for names, x in data:
            cur = int(((rest - prev) % x) * 10 / x)
            prev = rest % x
            if x == 10 and use_teens:
                plural = 2
                name.append(self.teens[cur])
            elif cur == 0:
                continue
            elif x == 10:
                name_ = names[cur]
                if isinstance(name_, tuple):
                    name_ = name_[0 if sex == 'm' else 1]
                name.append(name_)
                if cur >= 2 and cur <= 4:
                    plural = 1
                elif cur == 1:
                    plural = 0
                else:
                    plural = 2
            else:
                name.append(names[cur-1])
        return plural, name

    def num2text(self, num, main_units=((u'', u'', u''), 'm')):
        """
        http://ru.wikipedia.org/wiki/Gettext#.D0.9C.D0.BD.D0.BE.D0.B6.D0.B5.D1.81.\
        D1.82.D0.B2.D0.B5.D0.BD.D0.BD.D1.8B.D0.B5_.D1.87.D0.B8.D1.81.D0.BB.D0.B0_2
        """
        _orders = (main_units,) + self.orders
        if num == 0:
            return ' '.join((self.units[0], _orders[0][0][2])).strip() # ноль

        rest = abs(num)
        ord = 0
        name = []
        while rest > 0:
            plural, nme = self.thousand(rest % 1000, _orders[ord][1])
            if nme or ord == 0:
                name.append(_orders[ord][0][plural])
            name += nme
            rest = int(rest / 1000)
            ord += 1
        if num < 0:
            name.append(self.minus)
        name.reverse()
        return ' '.join(name).strip()


    def decimal2text(self, value, places=2,
                    int_units=(('', '', ''), 'm'),
                    exp_units=(('', '', ''), 'm')):
        value = decimal.Decimal(value)
        q = decimal.Decimal(10) ** -places

        integral, exp = str(value.quantize(q)).split('.')
        return u'{} {}'.format(
            self.num2text(int(integral), int_units),
            self.num2text(int(exp), exp_units))
