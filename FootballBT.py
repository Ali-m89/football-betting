import pandas as pd
import matplotlib.pyplot as plt
from statistics import mean

########################################################################################################################
#Specify league and league-specific parameters.
#Other league options could be added. E.g. LinkCode = 'E0' for English premier league, 'E1' for English championship
# league etc. (refer to football-data.co.uk).
League = 'Serie A'

if League == 'Serie A':
    TailCutOff = 172 #Number of oldest matches, to be used for predictions only.
    LinkCode = 'I1' #Code for link to historical data.
    APrCutOff = -0.2 #Projected goal difference cutoff, below which away team is predicted to win.
    ABetCutoff = -0.4 #Projected goal difference cutoff, below which away team is predicted to win (for betting).

########################################################################################################################
#Fetching historical data (2013-2024), from football-data.co.uk, into the dataframe DF.

DF = pd.DataFrame()
ylist = ['13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24']
yylist = [ylist[i] + ylist[i + 1] for i in range(len(ylist) - 1)]
yylist.reverse()

for ind in range(len(yylist)):
    yy = yylist[ind]
    DF1 = pd.read_csv("https://www.football-data.co.uk/mmz4281/" + yy + "/" + LinkCode + ".csv")
    DF1['FDate'] = pd.to_datetime(DF1['Date'], format='mixed',dayfirst=True)
    DF = pd.concat([DF, DF1], ignore_index=True)

DF.dropna(subset=['HomeTeam', 'FTHG', 'FTAG'], axis=0, inplace=True)
DF.sort_values(by=['FDate'], ascending=False, inplace=True)
DF.reset_index(drop=True, inplace=True)

########################################################################################################################
#Evaluating the projected goal difference between the home and away team, based on the teams' past performance.

SearchLength = 12 #How many months of data, prior to the match, to consider.

PDF = pd.DataFrame([], columns=['Date', 'HomeTeam', 'AwayTeam', 'PGDH', 'PGDA', 'PGD', 'Result', 'PResult', 'HGoals',
                                'AGoals', 'GD', 'B365H', 'B365D', 'B365A', 'Profit'])

for ind in range(len(DF)-TailCutOff):

    HTeam = DF['HomeTeam'][ind]
    ATeam = DF['AwayTeam'][ind]

    MDatepd = DF['FDate'][ind]
    PSD = MDatepd - pd.DateOffset(months=SearchLength)
    DFT = DF[(DF['FDate']>=PSD) & (DF['FDate']< MDatepd)]

    DFHTHT = DFT[DFT['HomeTeam']== HTeam]
    DFAWAW = DFT[DFT['AwayTeam']== ATeam]
    DFAWHT = DFT[DFT['HomeTeam']== ATeam]
    DFHTAW = DFT[DFT['AwayTeam']== HTeam]

    DFHT = pd.concat([DFHTHT, DFHTAW], ignore_index=True)
    DFAW = pd.concat([DFAWAW, DFAWHT], ignore_index=True)

    HTOPP1 = set(DFHTHT["AwayTeam"])
    HTOPP2 = set(DFHTAW["HomeTeam"])
    HTOPP = (HTOPP1 | HTOPP2) #Set of home team's opponents.

    AWOPP1 = set(DFAWHT["AwayTeam"])
    AWOPP2 = set(DFAWAW["HomeTeam"])
    AWOPP = (AWOPP1 | AWOPP2) #Set of away team's opponents.

    COPL = list(AWOPP.intersection(HTOPP)) #List of common opponents.

    DiffList = [0]
    DiffList2 = [0]

    for n in range(len(COPL)):
        COP = COPL[n]

        DFHTCOP1 = DFHT[DFHT['AwayTeam'] == COP]
        DFAWCOP1 = DFAW[DFAW['AwayTeam'] == COP]

        DFHTCOP2 = DFHT[DFHT['HomeTeam']== COP]
        DFAWCOP2 = DFAW[DFAW['HomeTeam'] == COP]

        HTCOPGDL =  (DFHTCOP1['FTHG'] - DFHTCOP1['FTAG']).tolist()
        ATCOPGDL = (DFAWCOP1['FTHG'] - DFAWCOP1['FTAG']).tolist()

        HTCOPGDL2 = (DFHTCOP2['FTAG'] - DFHTCOP2['FTHG']).tolist()
        ATCOPGDL2 =  (DFAWCOP2['FTAG'] - DFAWCOP2['FTHG']).tolist() 

        if len(ATCOPGDL) * len(HTCOPGDL) == 0:
            PGDH=0
        else:
            PGDH = (len(ATCOPGDL) * sum(HTCOPGDL) - len(HTCOPGDL) * sum(ATCOPGDL))/(len(ATCOPGDL) * len(HTCOPGDL))
            
        if len(ATCOPGDL2) * len(HTCOPGDL2) == 0:
            PGDA = 0
        else:
            PGDA = (len(ATCOPGDL2) * sum(HTCOPGDL2) - len(HTCOPGDL2) * sum(ATCOPGDL2))/(len(ATCOPGDL2) * len(HTCOPGDL2))

        DiffList.append(PGDH)
        DiffList2.append(PGDA)

        MPGDH = mean(DiffList) #Projected goal difference when both teams were home teams (against common opponents).
        MPGDA = mean(DiffList2) #Projected goal difference when both teams were away teams (against common opponents).
        PGD = (MPGDH + MPGDA)/2 #Projected goal difference.

#Placing bets, based on projected goal difference and evaluating the profit.
    BetSize = 1
    if PGD < ABetCutoff:
        if DF['FTR'][ind] == 'A':
            Profit = BetSize * (DF['B365A'][ind] - 1)
        else:
            Profit = BetSize * (-1)
    else:
        Profit = 0

#Making predictions based on projected goal difference.
    if PGD < APrCutOff:
        PFTR = 'A'
    else:
        PFTR = 'H'

#Updating the prediction dataframe.
    PDF.loc[len(PDF.index)] = [DF['FDate'][ind], DF['HomeTeam'][ind], DF['AwayTeam'][ind], MPGDH, MPGDA, PGD
        , DF['FTR'][ind], PFTR, DF['FTHG'][ind], DF['FTAG'][ind], DF['FTHG'][ind] - DF['FTAG'][ind],DF['B365H'][ind]
        , DF['B365D'][ind], DF['B365A'][ind], Profit]

########################################################################################################################
#Analysis

#Calculating Bet365 accuracy. (For some matches, teams have a 50-50 chance. We count half of these as correct.)
DF365H = PDF[(PDF['B365H'] < PDF['B365A']) & (PDF['Result'] == 'H')]
DF365A = PDF[(PDF['B365A'] < PDF['B365H']) & (PDF['Result'] == 'A')]
DF3655050 = PDF[PDF['B365H'] == PDF['B365A']]
B365Acc = (len(DF365H) + len(DF365A) + len(DF3655050)/2)/len(PDF)

#Calculating our model's accuracy.
CPDF = PDF[PDF['PResult']==PDF['Result']]
Acc = len(CPDF)/len(PDF)

MPGDHW = PDF[PDF['Result']=='H']['PGD'].mean() #Mean projected goal difference for home wins.
MPGDAW = PDF[PDF['Result']=='A']['PGD'].mean() #Mean projected goal difference for away wins.
MPGDD = PDF[PDF['Result']=='D']['PGD'].mean() #Mean projected goal difference for draws.

HWP = len(PDF[PDF['Result']=='H'])/len(PDF) #Percentage of home wins.
AWP = len(PDF[PDF['Result']=='A'])/len(PDF) #Percentage of away wins.
DP = len(PDF[PDF['Result']=='D'])/len(PDF) #Percentage of draws.

TP = PDF['Profit'].sum() #Total profit.
Attempts = len(PDF) - len(PDF[PDF['Profit']==0]) #Number of attempts at betting.
TB = Attempts * BetSize #Total bets.
ROI = TP/TB #Return on investment.


ADF = pd.DataFrame([[len(PDF), APrCutOff, ABetCutoff, Attempts,Attempts/len(PDF), TP, BetSize, ROI, Acc, B365Acc, HWP,
                     AWP, DP, MPGDHW, MPGDD, MPGDAW]], columns=['Matches', 'AWThreshold', 'AWThreshold(Bet)', 'Attempts'
    , 'Attempts%', 'Profit', 'BetSize', 'ROI', 'Accuracy', 'B365-Accuracy', 'HomeWin%', 'AwayWin%', 'Draw%', 'MPGDHW'
    , 'MPGDD', 'MPGDAW'])
########################################################################################################################
#Output
#Excel files:
PDF.to_excel(League + " Backtest.xlsx", index=False)
ADF.to_excel(League + " Backtest Analysis.xlsx", index=False)

#Cumulative profit plot:
PDF_reversed = PDF[::-1]
PDF_reversed.reset_index(drop=True, inplace=True)
PDF_reversed.loc[:,'Cumulative_Profit'] = PDF_reversed['Profit'].cumsum()
plt.figure(figsize=(10, 6))
plt.plot(PDF_reversed.index, PDF_reversed['Cumulative_Profit'])
plt.xlabel('Match')
plt.ylabel('Cumulative Profit')
plt.title('Cumulative Profit for ' + League)
plt.grid(True)
plt.savefig(League + ' Profit.png')

