listc=["London", "Rome", "Moscow", "Paris"]
nfile=open("towns.txt", 'w')

i = 0

for town in listc:
       nfile.write(town)
       if line == 2:
           nfile.write('\n')
           i = 0
           continue
       i += 1

nfile.close()
