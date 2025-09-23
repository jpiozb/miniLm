from sentence_transformers import SentenceTransformer
import os
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import socket
from urllib.parse import urlparse, urlunparse
import time

load_dotenv()

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def update_embeddings_logic(conn):
    """
    keywords.embedding이 null인 것들을 가져다가 64개씩 임베딩 벡터를 생성해서 keywords.embedding을 업데이트합니다.
    """
    total_updated_count = 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM keywords WHERE embedding IS NULL LIMIT 64")
            keywords_to_update = cur.fetchall()

            if not keywords_to_update:
                print("No more keywords to update.")
                return

            ids = [row[0] for row in keywords_to_update]
            names = [row[1] for row in keywords_to_update]

            print(f"Processing {len(names)} keywords: {names}")

            embeddings = model.encode(names)

            update_data = [(embedding.tolist(), keyword_id) for keyword_id, embedding in zip(ids, embeddings)]
            
            execute_batch(cur, "UPDATE keywords SET embedding = %s WHERE id = %s", update_data)
            
            updated_count = len(keywords_to_update)
            total_updated_count += updated_count
            conn.commit()
            print(f"Successfully updated {updated_count} keywords.")

    except (Exception, psycopg2.DatabaseError) as error:
        # If an error occurs, rollback the transaction
        if conn:
            conn.rollback()
        print(f"Error during update: {error}")
        # Re-raise the error to be caught by the main loop for connection re-establishment
        raise
    finally:
        # No conn.close() here, as connection is managed externally
        print(f"Total updated keywords in this run: {total_updated_count}")

if __name__ == "__main__":
    conn = None
    while True:
        try:
            if conn is None or conn.closed:
                print("Establishing new database connection...")
                postgres_url = os.environ["POSTGRES_URL"]
                print(f"Original POSTGRES_URL: {postgres_url}")

                # Parse the URL and resolve the hostname
                parsed_url = urlparse(postgres_url)
                hostname = parsed_url.hostname
                if hostname:
                    try:
                        ip_address = socket.gethostbyname(hostname)
                        print(f"Resolved {hostname} to {ip_address}")
                        # Create a new netloc with the IP address
                        new_netloc = f"{parsed_url.username}:{parsed_url.password}@{ip_address}:{parsed_url.port}"
                        # Reconstruct the URL with the IP address
                        postgres_url = urlunparse(parsed_url._replace(netloc=new_netloc))
                        print(f"New POSTGRES_URL: {postgres_url}")
                    except socket.gaierror as e:
                        print(f"Could not resolve hostname {hostname}: {e}. Proceeding with the original URL.")

                conn = psycopg2.connect(postgres_url)
                # Register pgvector for the connection
                from pgvector.psycopg2 import register_vector
                register_vector(conn)
                print("Database connection established.")

            update_embeddings_logic(conn)

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
            if conn and not conn.closed:
                conn.close()
            conn = None # Force re-establishment of connection

        print("\nWaiting for 1 second before the next run...\n")
        time.sleep(1)