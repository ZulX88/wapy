from neonize.client import NewClient
client = NewClient("db.sqlite3")

number = str(input('Nomor '))
client.PairPhone(number ,show_push_notification =True )