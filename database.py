from datetime import datetime
import shutil
import sqlite3


class Database:
    def __init__(self):
        pass

    def create(self):
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS offers(
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL
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
        conditions TEXT NOT NULL,
        sex TEXT NOT NULL
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
        self.cursor.execute('''
            INSERT INTO offers (id, date)
            SELECT 
                COALESCE(MAX(id), 0) + 1,
                date('now')
            FROM offers 
            WHERE date = date('now')
            UNION ALL
            SELECT 1, date('now')
            WHERE NOT EXISTS (
                SELECT 1 FROM offers WHERE date = date('now')
            )
            ORDER BY 1 DESC
            LIMIT 1
        ''')
        
        new_id = self.cursor.lastrowid
        print(new_id)
        return new_id
    
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
                            conditions,
                            sex
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    
    def export(self, source, target):
        shutil.copy2(source, target)
        
    def import_(self, source, target):
        try:
            print(source)
            self.otherConnection = sqlite3.connect(source)
            self.otherCursor = self.otherConnection.cursor()
            self.otherCursor.execute('SELECT * FROM customers')
            otherCustomers = self.otherCursor.fetchall()
            for customer in otherCustomers:
                self.open(target)
                self.createCustomer(customer[1:])
                self.save()
                
        except Exception as e:
            print(e)
            return -1
        
        
