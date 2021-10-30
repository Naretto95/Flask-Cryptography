#par lilian naretto et corentin Javaud
import string
import operator
phrase = input("phrase à décrypter : ")
print("1) caesar brute force")
print("2) caesar analyse de féquence")
print("3) Vigenere brute force")
print("4) Vigenere, sachant la taille de clé (13)")
option = input("methode de decryption :")

def cesar(chaine,decalage): # script encryptant avec la methode de cesar
    resultat=""
    chaine=chaine.upper()
    for lettre in chaine:
        if lettre in string.ascii_uppercase:
                resultat=resultat+string.ascii_uppercase[(string.ascii_uppercase.index(lettre)+decalage)%len(string.ascii_uppercase)]
        else:
            resultat+=lettre
    return resultat

def bruteforce(phrasee): #permet de decrypte en brute force, affiche les solutions possibles, a l'utilisateur d'analyser
    resultat=""
    i=25
    phrasee=phrasee.upper()
    while i >= 0:
        for lettre in phrasee:
            if lettre in string.ascii_uppercase:
                resultat=resultat+string.ascii_uppercase[(string.ascii_uppercase.index(lettre)+1)%len(string.ascii_uppercase)]
            else:
                resultat+=lettre
        print("clé = "+str(i)+" resultat="+resultat)
        i-=1
        phrasee=resultat
        resultat=""

def frequences(chaine): #permet d'obtenir les fréquences pour chaque lettre dans une phrase
    freq = [0] * 26
    for lettre in chaine:
        if lettre in string.ascii_uppercase:
            freq[string.ascii_uppercase.index(lettre)] += 1
    somme=sum(freq)
    i=0
    for nb in freq:
        freq[i] = nb / somme
        i+=1
    return freq

def analysis(chaine): #permet de comparer les frequences des lettres de la phrase et la frequence des lettres A et E dans les mots français, les 0 correspondent aux autres lettres, on cherche surtout les A et E
    francais = [900, 0, 0, 0, 1500,0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    correction = [0] * 26 
    for decalage in range(26):
        resultat = frequences(cesar(chaine, decalage))
        for freq, dic in zip(resultat,francais) :
            correction[decalage]+= freq*dic
    print("clé = " + str(26-correction.index(max(correction))) + " phrase décrypté : "+ cesar(chaine,correction.index(max(correction))))

def clecesar(chaine): #un peu comme au dessus, mais avec un tableu de frequence anglais
    anglais = [900, 0, 0, 0, 1500,0, 0, 0, 800, 0, 0, 300, 300, 700, 500,0, 0, 0, 700, 600, 200, 0, 0, 0, 0, 0]
    correction = [0] * 26 
    for decalage in range(26):
        resultat = frequences(cesar(chaine, decalage))
        for freq, dic in zip(resultat,anglais) :
            correction[decalage]+= freq*dic
    return 26-correction.index(max(correction))

def vigenere(chaine, n) : # utilise la methode de decryption cesar sur vigenere, on itère juste la methode
    resultat=""
    for i in range(n):
        resultat+=chr(65+ clecesar(chaine[i::n]))
    return resultat

def dechiffrevigenere(chaine, cle):
    taillecle = len(cle)
    i=0
    tabcle=[0]*taillecle
    tabchaine=[0]*len(chaine)
    for lettre in cle:
        tabcle[i]= ord(lettre)
        i+=1
    i=0
    for lettre in chaine:
        tabchaine[i]=ord(lettre)
        i+=1
    resultat = ''
    for i in range(len(tabchaine)):
        valeur = (tabchaine[i] - tabcle[i % taillecle]) % 26
        resultat += chr(valeur + 65)
    return resultat

if option == "1":
    bruteforce(phrase)
if option == "2":
    analysis(phrase)
if option == "3":
    phrase = phrase.replace(" ","")
    for i in range(1,20):
        print(vigenere(phrase,i))
if option == "4":
    phrase = phrase.replace(" ","")
    cle=vigenere(phrase,13)
    print("clé = "+cle +" resultat = "+dechiffrevigenere(phrase,cle))
