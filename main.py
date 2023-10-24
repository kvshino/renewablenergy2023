import matplotlib.pyplot as plt
def energy_request(profilo_di_carico,generazione_pannello,ora,E_b,E_max,E_min,E_grid):
    for i in ora:
        delta_Eb= generazione_pannello[i]- profilo_di_carico[i]

        if(delta_Eb>= 0):                   #produco più di quel che consumo
        
            if(E_b[i]+delta_Eb >= E_max):      #batteria piena ,vendo alla rete(in futuro accumulo sopra soglia)
                E_grid[i]=E_b[i]+delta_Eb-E_max
                E_b[i]=E_max

            if(E_b[i]+delta_Eb < E_max):        #batteria scarica ,la ricarico
                E_b[i]=E_b[i]+delta_Eb

        if(delta_Eb <0):                     #consumo più di quello che produco
            if(E_b[i] > E_min+delta_Eb):       #batteria piena ,vendo alla rete(in futuro accumulo sopra soglia)
                E_grid[i]=E_b[i]+delta_Eb-E_max
                E_b[i]=E_max

            if(E_b+delta_Eb < E_max):        #batteria scarica ,la ricarico
                E_b[i]=E_b[i]+delta_Eb

print("ciao aadasdasd")
#espressi in kw/h
profilo_di_carico= []
generazione_pannello=[]
ora=[]
E_b=[]
E_grid=[]
battery_level=[]



#popolamento 
E_max=5
E_min=1
profilo_di_carico= [1,1,1,1,1,1.75,  2.5,1.75,1,1,1,1,    1,1,1,1,1,1,      1.75,2.5,1.75,1.6,1.5,1]
generazione_pannello=[0,0,0,0,0,0,     0.5,0.75,1,1.6,2.25,3,      2.25,1.6,1,0.75,0.5,0,   0,0,0,0,0,0]

for i in range(0,24):
    ora.append(i)
    E_grid.append(0)
    E_b.append(E_min)

plt.plot(ora,profilo_di_carico, label='Carico di casa', color='blue', linestyle='--')
plt.xlabel('time')
plt.ylabel('Kw/h')
plt.title('Profilo di carico')
plt.legend()
plt.show()


plt.plot(ora,generazione_pannello, label='Generazione pannello', color='blue', linestyle='--')
plt.xlabel('time')
plt.ylabel('Kw/h')
plt.title('Generazione pannello')
plt.legend()
plt.show()
energy_request(profilo_di_carico,generazione_pannello,ora,E_min,E_max,E_min,E_grid)




