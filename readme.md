# Obsługa izochron

A plugin for QGIS by GIS-Support team.

# Aktualny stan, changelog

0.4a - tworzenie izochrony jako dodatkowego widoku
0.4 - dodano komunikat o nieznalezieniu węzła source (w zadanym promieniu)
0.3b - naprawiono błąd w funkcji updateDd powodujący korzystanie wyłącznie ze schemy public
0.3a - działa wybór schematu bazy. 
0.2 - wtyczka działa stabilnie w podstawowym zakresie
0.1 - startup

# Wymagania:

* QGIS >2.0 oraz python-qgis
* pgrouting >2.0
* psycopg2

# Instrukcja obsługi

Wybierz z listy bazę danych w której znajduje się tabela dla pgrouting, oraz funkcję której chcesz użyć.

* createDd

W tej funkcji plugin doda do istniejącej bazy tabelę "catchment" oraz widoki "catchment_final" oraz "points_min".
Przed uruchomieniem funkcji trzeba również uzupełnić pola opisujące tabelę z siecią routingu.
Dla importera osm2po typowe wartości są następujące:

schema: public  
edge_table: osm_2po_4pgr  
geometry: geom_way  

id: id  
source: source  
target: target  
cost: cost  

Następnie wybieramy numer węzła startowego wpisując go ręcznie w polu source_id lub klikając w zielony krzyżyk, a następnie na mapie. Operacja ta wymaga cierpliwości, trwa nawet kilka sekund, ale automatycznie uzupełni pole source_id o najbliższy węzeł sieci. W oknie distance wpisujemy wartość w godzinach, dla której chcemy obliczyć osiągalne odcinki sieci.

* updateDd

Ta funkcja działa bardzo podobnie jak createDd, jedyna różnica taka że nie tworzy tabeli catchment - bez której obliczenia nie dojdą do skutku (konieczne jest wcześniejsze jednorazowe uruchomienie funkcji createDd). 

* clearDd

Ta funkcja musi mieć prawidłowo wybraną wyłącznie bazę danych, pozostałe pola powinny być wypełnione, lecz nie mają znaczenia. Czyści ona tabelę catchment, a w związku z jej definicją również kaskadowo widoki. Pozwala to na szybkie rozpoczęcie nowej analizy.

* isochrones

Tworzenie izochrony czasu dojazdu, jako widok z concavehull. W polu wpisz wartość w minutach.

* dodatkowe informacje

Czas podawany w polu cost wtyczki wyrażony jest w godzinach, zaś wyniki działania bezpośrednio w minutach. Wyszukiwanie węzła startowego odbywa się w promieniu 10 pikseli mapy w aktualnym odwzorowaniu. W przypadku nie odnalezienia w zadanym promieniu żadnego węzła, wtyczka poda komunikat.

# Prawa autorskie i licencje

Przy opracowaniu wtyczki wykorzystano plugin pgRouting_Layer (https://github.com/anitagraser/pgRoutingLayer) na licencji GNU GPL 2.
Kod SQL zapytań - (C) Michał Mackiewicz, 2014.
