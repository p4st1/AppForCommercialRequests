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
        date TEXT NOT NULL,
        )
        """
        )

        self.cursor.execute(
            '''
        CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        surname TEXT NOT NULL, 
        patronymic TEXT NOT NULL,
        address TEXT NOT NULL,
        email TEXT NOT NULL,
        phoneNumber TEXT NOT NULL,
        companyName TEXT NOT NULL,
        post TEXT NOT NULL,
        conditions TEXT NOT NULL
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
        id = self.cursor.fetchone()[0]
        offerName = f'{id}/{datetime.now().strftime('%d.%m')}'
        print(offerName)
        self.cursor.execute('''INSERT INTO offers (
                            date
                            ) VALUES (?)
                        ''', (datetime.now().strftime('%d.%m'), ))
        return id
    
    def createCustomer(self, data):
        self.cursor.execute('''INSERT INTO customers (
                            name, 
                            surname, 
                            patronymic, 
                            address,
                            email, 
                            phoneNumber, 
                            companyName,
                            post,
                            conditions
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', data)
    
    def getAllCustomers(self):
        try:
            self.cursor.execute('SELECT * FROM customers')
            customers = self.cursor.fetchall()
        except:
            return -1
        else:
            return customers
        
    def getCustomer(self, name):
        try:
            self.cursor.execute(f'SELECT * FROM customers WHERE companyName = ?', (name, ))
            customers =  self.cursor.fetchall()
        except:
            return -1
        else:
            return customers
        
    def delCustomer(self, name):
        try:
            self.cursor.execute(f'DELETE FROM customers WHERE companyName = ?', (name, ))
        except:
            return -1