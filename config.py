class Config:
    types = {
            '%': 'percents',
            '*': 'multiply',
            '/': 'division'
        }
    
    isTableOpened = False

    settings = {
        
    }
    
    config = {
        
    }

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
