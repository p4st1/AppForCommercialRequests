import shutil
import json
from pathlib import Path
from config import Config
import time
import decimal
import json
import sys
import os

class DatabaseTools:
    def __init__(self):
        pass

    @staticmethod
    def phoneNumToStr(num):
        num = str(num)
        return f'+{num[0]} ({num[1:4]}) {num[4:7]}-{num[7:9]}-{num[9:]}'
    
    @staticmethod
    def evalWithVars(line):
        paramsData = DatabaseTools.load_json(Config.vars_path)
        res = ''
        for i in line.split('$'):
            print(res)
            for key, val in paramsData['parameters'].items():
                variable, value, calc = val
                if i == variable:
                    if calc == 'percents':
                        res += f'*{value}/100'
                        break
                    else:        
                        res += f'{DatabaseTools.getCalc(calc)}{value}'
                        break
            else:
                res += i
        
        if res[0] in '+*/':
            res = res[1:]
            
        return round(eval(f'{res}'), 4)
    
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
            float(value)
        except:
            return None
        else:
            return float(value)
        
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
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_json_atomic(path: Path, data: dict) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)
        
    @staticmethod
    def write_log(message):
        with open(Config.log_path, 'a', encoding='utf-8') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
        
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