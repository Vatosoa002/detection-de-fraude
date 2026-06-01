import networkx as nx
import random 
from neo4j import GraphDatabase
import math

URI="bolt://localhost:7687"
USER="neo4j"
PASSWORD=input("Entrer le mot de passe neo4j: ")

driver=GraphDatabase.driver(URI,auth=(USER,PASSWORD))

def generer_graphe(n,p):
    G=nx.Graph() #graphe non oriente

    #creer les noeuds
    for i in range(1,n+1):
        G.add_node(i)

    for i in G.nodes():
        if i==1:
            continue
        voisin=random.randint(1,i-1)
        G.add_edge(i,voisin)
    
    for i in G.nodes():
        for j in range(i+1,n+1):
            r=random.random()
            if r>p or G.has_edge(i,j):
                continue
            else:
                G.add_edge(i,j)
    
    return G

def dfs_clique(G,clique,candidats,cliques):
    if not candidats:
        cliques.append(frozenset(clique))
        return

    extension=False
    for v in list(candidats):
        extension=True
        nouvelle_clique=clique+[v]
        voisins_v=set(G.neighbors(v))
        nouveaux_candidats=candidats & voisins_v
        nouveaux_candidats.discard(v)
        dfs_clique(G,nouvelle_clique,nouveaux_candidats,cliques)
        candidats.remove(v)

    if not extension:
        cliques.append(frozenset(clique))

def trouver_cliques_maximales(G):
    cliques=[]
    for sommet in G.nodes():
        candidats=set(G.neighbors(sommet))
        dfs_clique(G,[sommet],candidats,cliques)
    
    cliques=list(set(cliques))
    maximales=[]
    for c1 in cliques:
        maximale=True
        for c2 in cliques:
            if c1!=c2 and c1<c2:
                maximale=False
                break

        if maximale:
            maximales.append(set(c1))
    
    return maximales

def creer_communaute_et_lien(personne,community_id):
    with driver.session() as session:
        session.run(
            """
            MERGE (c:Community {id: $cid})
            MERGE (p:Personne {id: $name})
            MERGE (p)-[:IN_COMMUNITY]->(c)
            """, 
            name=str(personne), cid=community_id
        )

def creer_personne_et_lien(G):
    with driver.session() as session:
        #vider la base
        session.run("MATCH (n) DETACH DELETE n")

        for n in G.nodes():
            session.run(
                "CREATE (:Personne {id: $id})",
                id=str(n)
            )

        for a,b in G.edges():
            session.run(
                """
                MATCH (a:Personne {id: $a}),(b:Personne {id: $b})
                CREATE (a)-[:CONNAIT]->(b)
                CREATE (b)-[:CONNAIT]->(a)
                """,
                a=str(a),b=str(b)
            )

if __name__ == "__main__":
    n=int(input("Entrer la taille du graphe: "))
    G=generer_graphe(n,p=math.log(n)/n)
    communautes=trouver_cliques_maximales(G)
    creer_personne_et_lien(G)
    for i,clique in enumerate(communautes):
        for n in clique:
            creer_communaute_et_lien(n,i)