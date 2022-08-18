import mysql.connector

# DB에 접근하여 미세한 조작이 필요한 경우 해당 클래스를 사용합니다.

class DBManager:
    def __init__(self):
        self.mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="MM"
        )
        self.mycursor = self.mydb.cursor()

        # 테이블 정보
        self.dealTable = "DEAL_TABLE"
        self.underlyingTable = "UNDERLYING_TABLE"


    def bulkInsert(self, table, param, val):
        length = '%s, ' * len(param)
        sql = f"INSERT INTO {table} ({', '.join(param)}) VALUES ({length[:-2]})"
        print(sql)
        self.mycursor.executemany(sql, val)
        self.mydb.commit()
        print(self.mycursor.rowcount, "record inserted.")




if __name__ == "__main__":
    dbmanager = DBManager()

    # val = [("John", "Highway 21"), ("John", "Highway 21")]
    # param = ('', 'name', 'inseud')
    # dbmanager.bulkInsert("UNDERLYING_TABLE", param, val)
