class Config:
    DEFAULT_OFFER_VALIDITY_DAYS = 10
    OFFER_VALIDITY_MIN_DAYS = 1
    OFFER_VALIDITY_MAX_DAYS = 365

    DEFAULT_PAYMENT_TEMPLATES = [
        "на дату подписания спецификации Поставщиком",
        "на дату оплаты",
    ]

    DEFAULT_SETTINGS = {
        "closeTable": True,
        "autoFill": True,
        "autoFillWebAuth": False,
        "openUpdateTab": True,
        "openLastTab": True,
        "testFeature": False,
        "skip_auto_trade_warning": False,
        "use_auto_trade_timer": False,
        "auto_trade_timer_minutes": 30,
        "developer_skip_table_fill_errors": False,
        "show_retrade_tab": True,
        "show_platform_tab": True,
        "show_submission_tab": True,
        "show_history_tab": True,
        "show_updates_tab": True,
    }

    DEFAULT_CONFIG = {
        "logisticVar": "0",
        "logisticNum": "1",
        "customNum": "1",
        "termDelivery": "0",
        "markup": "1",
        "requestNumber": "",
        "pathToSaveCP": "",
        "pathToSaveExcel": "",
        "pathToDB": "",
        "ExcelIndent": "0",
        "lastTable": "",
        "offerValidityDays": str(DEFAULT_OFFER_VALIDITY_DAYS),
        "lastCreateDocFields": {},
        "paymentTemplates": DEFAULT_PAYMENT_TEMPLATES.copy(),
        "platformLogin": "",
        "platformPassword": "",
    }

    types = {
            '%': 'percents',
            '*': 'multiply',
            '/': 'division'
        }

    isTableOpened = False

    settings = DEFAULT_SETTINGS.copy()
    config = DEFAULT_CONFIG.copy()

    cfg_path = ''
    db_path = ''
    vars_path = ''
    template_path = ''
    template_docx_path = ''
    template_docx_path_short = ''
    log_path = ''
    logo_path = ''

    currencySymb = ('¥', '$', '₽')
    currency = {
        '¥': ('CNY',
               ((u'юань', u'юаня', u'юаней'), 'm'),
               ((u'фэнь', u'фэня', u'фэней'), 'f')
        ),
        '$': ('USD',
               ((u'доллар', u'доллара', u'долларов'), 'm'),
               ((u'цент', u'цента', u'центов'), 'f')
        ),
        '₽': ('RUB',
               ((u'рубль', u'рубля', u'рублей'), 'm'),
               ((u'копейка', u'копейки', u'копеек'), 'f')
        ),
        '€': ('EUR',
              ((u'евро', u'евро', u'евро'), 'm'),
              ((u'евроцент', u'евроцента', u'евроцентов'), 'f')
        )
    }

    testFeature = False

    @classmethod
    def normalize_offer_validity_days(cls, raw_value=None) -> int:
        if raw_value is None:
            raw_value = cls.DEFAULT_OFFER_VALIDITY_DAYS
        try:
            days = int(float(str(raw_value).strip().replace(",", ".")))
        except (TypeError, ValueError):
            days = cls.DEFAULT_OFFER_VALIDITY_DAYS
        return max(cls.OFFER_VALIDITY_MIN_DAYS, min(cls.OFFER_VALIDITY_MAX_DAYS, days))

    @classmethod
    def get_offer_validity_days(cls) -> int:
        return cls.normalize_offer_validity_days(
            cls.config.get("offerValidityDays", cls.DEFAULT_OFFER_VALIDITY_DAYS)
        )
