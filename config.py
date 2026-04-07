class Config:
    DEFAULT_PAYMENT_TEMPLATES = [
        "на дату подписания спецификации Поставщиком",
        "на дату оплаты",
    ]

    DEFAULT_SETTINGS = {
        "closeTable": True,
        "autoFill": True,
        "openUpdateTab": True,
        "openLastTab": True,
        "testFeature": False,
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
        "paymentTemplates": DEFAULT_PAYMENT_TEMPLATES.copy(),
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
