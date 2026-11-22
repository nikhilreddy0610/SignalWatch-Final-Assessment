from cassandra.cluster import Cluster

from app.config import CASSANDRA_CONTACT_POINTS, CASSANDRA_KEYSPACE


def get_cluster():
    return Cluster(contact_points=CASSANDRA_CONTACT_POINTS, port=9042)


def get_session():
    cluster = get_cluster()
    session = cluster.connect()
    session.set_keyspace(CASSANDRA_KEYSPACE)
    return session
