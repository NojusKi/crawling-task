SOFT_FIELDS=("egzaminotip", "sesija", "lygis", "srautas", "dalis") #Laukai, kurie negali prieštarauti vienas kitam

def rasti_rakta(uzduotis, raktai):
    ivertinti = [] # taskai raktai
    for raktas in raktai:
        if (raktas["family"], raktas["year"], raktas["dalykas"]) != (uzduotis["family"], uzduotis["year"], uzduotis["dalykas"]):
            continue
        if raktas["rusis"] != uzduotis["rusis"]: # rusis t.y. tipas turi sutapti pavyzdine, kurtiesiems....
            continue
        #darb dalis t.y. rasymas, testas turi sutapti
        if raktas["darbo_dalis"] and uzduotis["darbo_dalis"] and raktas["darbo_dalis"] != uzduotis["darbo_dalis"]:
            continue
        taskai = 0
        for laukas in SOFT_FIELDS:
            a, b = uzduotis[laukas], raktas[laukas]
            if a and b:
                if a != b:
                    break
                taskai += 1
        else:
            ivertinti.append((taskai,raktas))
            
    geriausias = max((t for t, _ in ivertinti), default=0)
    nugaletojai = {r["url"]: r for t, r in ivertinti if t == geriausias}
    return next(iter(nugaletojai.values())) if len(nugaletojai) == 1 else None