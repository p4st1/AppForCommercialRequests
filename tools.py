import ast
import decimal
import json
import os
import re
import shutil
import sys
import time
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

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return float(node.value)
            if isinstance(node, ast.Num):
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
    def merge_config_with_defaults(raw_data: dict | None) -> dict:
        data = raw_data if isinstance(raw_data, dict) else {}
        raw_config = data.get("config", {})
        raw_settings = data.get("settings", {})

        config = Config.DEFAULT_CONFIG.copy()
        if isinstance(raw_config, dict):
            config.update(raw_config)

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
        config["ExcelIndent"] = str(config.get("ExcelIndent", "0"))
        config["lastTable"] = str(config.get("lastTable", "")).strip()
        config["pathToSaveCP"] = str(config.get("pathToSaveCP", "")).strip()
        config["pathToSaveExcel"] = str(config.get("pathToSaveExcel", "")).strip()

        settings = Config.DEFAULT_SETTINGS.copy()
        if isinstance(raw_settings, dict):
            for key in settings:
                settings[key] = DatabaseTools._to_bool(raw_settings.get(key), settings[key])

        return {"config": config, "settings": settings}
    
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
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

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
        try:
            float(str(value).replace(",", ".").replace(" ", ""))
        except Exception:
            return None
        else:
            return float(str(value).replace(",", ".").replace(" ", ""))

    @staticmethod
    def parse_int(value, field_name: str, allow_zero=True) -> int:
        normalized = str(value).strip().replace(" ", "").replace(",", ".")
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
        normalized = str(value).strip().replace(" ", "").replace(",", ".")
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
    def user_data_dir(app_name: str) -> Path:
        if sys.platform.startswith("win"):
            return Path(os.environ["APPDATA"]) / app_name
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / app_name
        return Path.home() / ".local" / "share" / app_name

    @staticmethod
    def ensure_user_file(app_name: str, template_rel_path: str, target_name: str, f=0) -> Path:
        dst_dir = DatabaseTools.user_data_dir(app_name)
        dst_dir.mkdir(parents=True, exist_ok=True)

        dst = dst_dir / target_name
        if not dst.exists():
            src = DatabaseTools.resourcePath(template_rel_path)
            shutil.copy2(src, dst)
         
        if f:
            src = DatabaseTools.resourcePath(template_rel_path)
            shutil.copy2(src, dst)
            
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
    def write_log(message):
        with open(Config.log_path, 'a', encoding='utf-8') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")

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
        num = num[::-1]
        num = [num[i : i + 3] for i in range(0, len(num), 3)]
        res = ''
        for i in num[::-1]:
            res += f'{i[::-1]} '
        return f'{res.strip()},{mantissa.zfill(2)}'

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

    if __name__ == '__main__':
        import sys
        if len(sys.argv) > 1:
            try:
                num = sys.argv[1]
                if '.' in num:
                    print(decimal2text(
                        decimal.Decimal(num),
                        int_units=((u'штука', u'штуки', u'штук'), 'f'),
                        exp_units=((u'кусок', u'куска', u'кусков'), 'm')))
                else:
                    print(num2text(
                        int(num),
                        main_units=((u'штука', u'штуки', u'штук'), 'f')))
            except ValueError:
                print (sys.stderr, "Invalid argument {}".format(sys.argv[1]))
            sys.exit()
