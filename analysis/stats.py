from sqlalchemy.orm import Session
from sqlalchemy import text


def show_stats(session: Session):
    hub_count = session.execute(text("""
        SELECT count(*) FROM pages p
        JOIN urls u ON p.url_id = u.id
        WHERE u.url LIKE '%/ru/hubs/%/articles%'
    """)).scalar()

    article_count = session.execute(text("""
        SELECT count(*) FROM pages p
        JOIN urls u ON p.url_id = u.id
        WHERE u.url SIMILAR TO '%/ru/articles/[0-9]+/%'
           OR u.url SIMILAR TO '%/ru/companies/%/articles/[0-9]+/%'
    """)).scalar()

    total = session.execute(text("SELECT count(*) FROM pages")).scalar()
    print(f"Всего страниц: {total}")
    print(f"  Хаб-страницы (списки статей): {hub_count}")
    print(f"  Статьи: {article_count}")

    print("\n=== Ссылки (только из статей) ===")
    links_by_type = session.execute(text("""
        SELECT l.is_internal, count(*) FROM links l
        JOIN pages p ON l.from_page_id = p.id
        JOIN urls u ON p.url_id = u.id
        WHERE u.url SIMILAR TO '%/ru/articles/[0-9]+/%'
           OR u.url SIMILAR TO '%/ru/companies/%/articles/[0-9]+/%'
        GROUP BY l.is_internal
    """)).fetchall()
    for row in links_by_type:
        label = "Внутренние" if row[0] else "Внешние"
        print(f"  {label}: {row[1]}")

    statuses = session.execute(text("SELECT status, count(*) FROM frontier GROUP BY status")).fetchall()
    print("\nСтатус очереди:")
    for row in statuses:
        print(f"  {row[0]}: {row[1]}")

    print("\n=== Топ-10 внешних доменов (из статей) ===")
    top10_external_hosts = session.execute(text("""
        SELECT u2.host, count(*) as cnt
        FROM links l
        JOIN pages p ON l.from_page_id = p.id
        JOIN urls u1 ON p.url_id = u1.id
        JOIN urls u2 ON l.to_url_id = u2.id
        WHERE l.is_internal = False
          AND (u1.url SIMILAR TO '%/ru/articles/[0-9]+/%'
               OR u1.url SIMILAR TO '%/ru/companies/%/articles/[0-9]+/%')
        GROUP BY u2.host ORDER BY cnt DESC LIMIT 10
    """)).fetchall()
    for i, row in enumerate(top10_external_hosts, 1):
        print(f"  {i}. {row[0]:<30} {row[1]}")

    print("\n=== Топ-10 anchor-текстов (из статей) ===")
    top_anchors = session.execute(text("""
        SELECT l.anchor_text, count(*) as cnt
        FROM links l
        JOIN pages p ON l.from_page_id = p.id
        JOIN urls u ON p.url_id = u.id
        WHERE l.anchor_text != ''
          AND (u.url SIMILAR TO '%/ru/articles/[0-9]+/%'
               OR u.url SIMILAR TO '%/ru/companies/%/articles/[0-9]+/%')
        GROUP BY l.anchor_text ORDER BY cnt DESC LIMIT 10
    """)).fetchall()
    for i, row in enumerate(top_anchors, 1):
        print(f"  {i}. {row[0]:<40} {row[1]}")

    print("\nHTTP-статусы")
    statuses = session.execute(text("""
        SELECT http_status, count(*) as cnt
        FROM pages GROUP BY http_status ORDER BY cnt DESC
    """)).fetchall()
    for row in statuses:
        status = row[0] if row[0] else "N/A"
        print(f"  {status}: {row[1]}")

    print("\nГлубина обхода")
    depths = session.execute(text("""
        SELECT depth, status, count(*) as cnt
        FROM frontier GROUP BY depth, status ORDER BY depth, status
    """)).fetchall()
    for row in depths:
        print(f"  depth={row[0]}, status={row[1]}: {row[2]}")

    print("\n=== Топ-10 самых ссылочных статей ===")
    top_articles = session.execute(text("""
        SELECT p.title, count(*) as cnt
        FROM links l
        JOIN pages p ON l.from_page_id = p.id
        JOIN urls u ON p.url_id = u.id
        WHERE u.url SIMILAR TO '%/ru/articles/[0-9]+/%'
           OR u.url SIMILAR TO '%/ru/companies/%/articles/[0-9]+/%'
        GROUP BY p.title ORDER BY cnt DESC LIMIT 10
    """)).fetchall()
    for i, row in enumerate(top_articles, 1):
        title = row[0][:60] if row[0] else "N/A"
        print(f"  {i}. {title:<60} ссылок: {row[1]}")
