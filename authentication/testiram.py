def checkJMBG(jmbg):
    OK=True;
    dan=int(jmbg[0])*10+int(jmbg[1]);
    mesec=int(jmbg[2])*10+int(jmbg[3]);
    # godina = int(jmbg[4]) * 100 + int(jmbg[5])*10+int(jmbg[6]);
    region=int(jmbg[7])*10+int(jmbg[8]);
    # broj=int(jmbg[9]) * 100 + int(jmbg[10])*10+int(jmbg[11]);
    # kontrolna=int(jmbg[12]);
    if(dan>31 or mesec>12 or region<70  ):
        OK=False;
    return OK;


def checkPassword(password):
    val = True;

    if len(password) < 8:
        val = False
    if not any(char.isdigit() for char in password):
        val = False
    if not any(char.isupper() for char in password):
        val = False
    if not any(char.islower() for char in password):
        val = False

    return val;

if __name__ == '__main__':

    jmbg="1212567891234";
    print(checkPassword("aaaaAA1"));
