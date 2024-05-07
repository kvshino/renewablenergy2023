from datetime import *
import pandas as pd
import random


def get_true_load_consumption():
    """
        Returns a dataframe containing the load consumption history.
        From the actual hour back to the earliest ones.
        """

    try:
        df = pd.read_csv("csv/consumptions.csv")
    
        now = datetime.now()

        one_month_ago = datetime.now() - timedelta(days=30)

        # Filtra il DataFrame fino alla data e all'ora attuali
        df_troncato = df[((pd.to_datetime(df['data'], format='%Y%m%d') < pd.to_datetime(now.strftime('%Y%m%d'))) |
                        ((pd.to_datetime(df['data'], format='%Y%m%d') == pd.to_datetime(now.strftime('%Y%m%d'))) &
                        (df['ora'] <= now.hour))) &
                            (pd.to_datetime(df['data'], format='%Y%m%d') > pd.to_datetime(one_month_ago.strftime('%Y%m%d')))]
        
        if(df_troncato.empty == True):
            create_dummy_database_consumption("csv/consumptions.csv")
            df_troncato = pd.read_csv("csv/consumptions.csv")

    except(Exception):
            create_dummy_database_consumption("csv/consumptions.csv")
            df_troncato = pd.read_csv("csv/consumptions.csv")
        

    return df_troncato


def get_estimate_load_consumption(dataframe: pd.DataFrame):
    """
        Returns the consumption estimate of the load.

        df.loc[1, 'consumo']

        From the next hour up to the 24h.
    """
    media_oraria = dataframe.groupby("ora")["consumo"].mean()

    dataframe['data'] = pd.to_datetime(dataframe['data'], format='%Y%m%d')

    dataframe['giorno'] = dataframe['data'].dt.day_name()

    next_hour = datetime.now() + timedelta(hours=1) - timedelta(minutes=datetime.now().minute)
    oggi = (next_hour).strftime("%A")
    domani = (next_hour + timedelta(days=1)).strftime("%A")

    dataframe = dataframe[(dataframe['giorno'] == oggi) | (dataframe['giorno'] == domani)]

    media_giorno_target = dataframe.groupby("ora")["consumo"].mean()

    df = pd.DataFrame((media_oraria + media_giorno_target) / 2).reset_index()
    df = pd.concat([df.iloc[next_hour.hour:], df.iloc[:next_hour.hour]])

    df.reset_index(drop=True, inplace=True)

    return df




def create_dummy_database_consumption(file_name="csv/dummy_database.csv"):

    one_month_ago = datetime.now() - timedelta(days=30)

    with open(file_name, 'w+') as file:
        file.write("data,ora,consumo")

        for i in range(30):
            for j in range(24):
                    match(j):
                        case 0:
                            value = random.randint(150, 200)
                        case 1:
                            value = random.randint(500, 600)
                        case 2:
                            value = random.randint(250, 300)
                        case 3:
                            value = random.randint(150, 220)
                        case 4:
                            value = random.randint(150, 200)
                        case 5:
                            value = random.randint(150, 200)
                        case 6:
                            value = random.randint(150, 200)
                        case 7:
                            value = random.randint(550, 650)
                        case 8:
                            value = random.randint(250, 300)
                        case 9:
                            value = random.randint(250, 300)
                        case 10:
                            value = random.randint(170, 200)
                        case 11:
                            value = random.randint(170, 200)
                        case 12:
                            value = random.randint(170, 200)
                        case 13:
                            value = random.randint(1100, 1250)
                        case 14:
                            value = random.randint(700, 800)
                        case 15:
                            value = random.randint(650, 700)
                        case 16:
                            value = random.randint(250, 350)
                        case 17:
                            value = random.randint(250, 350)
                        case 18:
                            value = random.randint(1100, 1200)
                        case 19:
                            value = random.randint(1250, 1300)
                        case 20:
                            value = random.randint(650, 700)
                        case 21:
                            value = random.randint(800, 900)
                        case 22:
                            value = random.randint(550, 600)
                        case 23:
                            value = random.randint(280, 320)


                    file.write('\n' + str((one_month_ago + timedelta(days=i)).strftime('%Y%m%d')) + "," + str(j) + "," + str(value))
        file.close()