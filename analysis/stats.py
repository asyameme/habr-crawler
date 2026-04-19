from sqlalchemy.orm import Session
from sqlalchemy import text


def show_stats(session: Session):
    num_of_pages = session.execute(text("SELECT count(*) FROM pages;")).scalar()
    print(f"Всего обработано {num_of_pages} уникальных страниц")

    links_by_type = session.execute(text("SELECT is_internal, count(*) FROM links GROUP BY is_internal")).fetchall()
    print("\nСсылки: ")
    for row in links_by_type:
        label = "Внутренние" if row[0] else "Внешние"
        print(f"  {label}: {row[1]}")

    statuses = session.execute(text("SELECT status, count(*) FROM frontier GROUP BY status")).fetchall()
    print("\nСтатус очереди:")
    for row in statuses:
        print(f"  {row[0]}: {row[1]}")

    top10_external_hosts = session.execute(text("""SELECT u.host, count(*) as cnt
                                                FROM links l JOIN urls u ON l.to_url_id = u.id
                                                WHERE l.is_internal = False
                                                GROUP BY u.host ORDER BY cnt DESC LIMIT 10;""")).fetchall()
    print("\nТоп-10 внешних доменов")
    for i, row in enumerate(top10_external_hosts, 1):
        print(f"  {i}. {row[0]:<30} {row[1]}")

    print("\nТоп-10 anchor-текстов")
    top_anchors = session.execute(text("""SELECT anchor_text, count(*) as cnt
                                            FROM links WHERE anchor_text != ''
                                            GROUP BY anchor_text ORDER BY cnt DESC LIMIT 10""")).fetchall()
    for i, row in enumerate(top_anchors, 1):
        print(f"  {i}. {row[0]:<40} {row[1]}")

    print("\nHTTP-статусы")
    statuses = session.execute(text("""SELECT http_status, count(*) as cnt
                                        FROM pages GROUP BY http_status ORDER BY cnt DESC""")).fetchall()
    for row in statuses:
        status = row[0] if row[0] else "N/A"
        print(f"  {status}: {row[1]}")

    print("\nГлубина обхода")
    depths = session.execute(text("""SELECT depth, status, count(*) as cnt
                                        FROM frontier GROUP BY depth, status ORDER BY depth, status""")).fetchall()
    for row in depths:
        print(f"  depth={row[0]}, status={row[1]}: {row[2]}")

    print("\n=== Топ-10 самых ссылочных статей ===")
    top_articles = session.execute(text("""SELECT p.title, count(*) as cnt
                                            FROM links l JOIN pages p ON l.from_page_id = p.id
                                            GROUP BY p.title ORDER BY cnt DESC LIMIT 10""")).fetchall()
    for i, row in enumerate(top_articles, 1):
        title = row[0][:60] if row[0] else "N/A"
        print(f"  {i}. {title:<60} ссылок: {row[1]}")

    


    