from datetime import datetime
import sqlite3


class Database:
    def __init__(self):
        pass

    def create(self):
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS offers(
        id INTEGER PRIMARY KEY,
         TEXT NOT NULL,
        password TEXT NOT NULL,
        email TEXT NOT NULL,
        fullname TEXT NOT NULL
        )
        """
        )

        self.cursor.execute(
            '''
        CREATE TABLE IF NOT EXISTS suppliers(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        TIN INTEGER NOT NULL,
        phoneNumber INTEGER NOT NULL,
        website TEXT NOT NULL,
        addresIndex INTEGER NOT NULL,
        room INTEGER NOT NULL,
        building INTEGER NOT NULL,
        RRC INTEGER NOT NULL,
        img TEXT NOT NULL
        )
            '''
        )

    def open(self, filename: str):
        try:
            self.connection = sqlite3.connect(filename)
        except:
            return -1
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    def save(self):
        self.connection.commit()

    def createOffer(self):
        self.cursor.execute("SELECT MAX(id) FROM offers")
        offerName = f'{self.cursor.fetchone()[0]}/{datetime.now().strftime('%d.%m')}'
        print(offerName)
        self.cursor.execute('''INSERT INTO offers
                        ''')
        
    def createSupplier(self, data):
        self.cursor.execute('''INSERT INTO suppliers (
                            name, 
                            email, 
                            address, 
                            city,
                            TIN, 
                            phoneNumber, 
                            website, 
                            addresIndex, 
                            room, 
                            building, 
                            RRC, 
                            img
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', data)
    
    def getAllSuppliers(self):
        try:
            self.cursor.execute('SELECT * FROM suppliers')
            suppliers = self.cursor.fetchall()
        except:
            return -1
        else:
            return suppliers
        
    def getSupplier(self, name):
        try:
            self.cursor.execute(f'SELECT * FROM suppliers WHERE name = ?', (name, ))
            suppliers =  self.cursor.fetchall()
        except:
            return -1
        else:
            return suppliers

        
test = ['ООО "АЛЬФА ИНЖИНИРИННГ', 
        'admin@alphakappa.ru', 
        'ул. рябиновая',
        'г. Москва',
        '3717342374',
        '89334728200',
        'alphakappa.ru',
        '660028',
        '26',
        '1',
        '485874395',
        'None']