import sqlite3

database_name = 'reddit'
table_name = 'comments'

conn = sqlite3.connect(database_name)
c = conn.cursor()

def printTable():
    c.execute("Select * from " + table_name)
    data = c.fetchall()
    for i in data:
        print(i)

def printDetailsFromId(id):
    c.execute("Select * from " + table_name + " where id = ?",(id,))
    data = c.fetchall()
    if len(data) == 0:
        print("This id doesn't exist in table\n")
    else:
        print(data[0])

if __name__ == "__main__":
    
    while True:
        print("Choose options from below(only integers) : ")
        print("1 if you want to print table")
        print("2 for details of one comment id")
        print("0 for exit")
        print()

        inp = int(input())
        
        if inp == 0:
            break
        elif inp == 1:
            printTable()
            print()
        elif inp == 2:
            id = input("Enter id for details : ")
            printDetailsFromId(id)
            print()
        else:
            continue

