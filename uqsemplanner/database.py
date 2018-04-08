from uqsemplanner import app
from uqsemplanner import scripts

import sqlite3
from flask import g, abort

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.cli.command('populatedb_course')
def populatedb_course_command():
    courses = scripts.course.scrape()
    
    db = get_db()
    db.execute('delete from courses')
    for course in courses:
        db.execute('insert into courses (code, title) values (?, ?)',
                [course.code, course.title])
    db.commit()
    print('Populated database with courses')

@app.cli.command('populatedb_program')
def populatedb_program_command():
    programs = scripts.program.scrape()
    majors = {}

    db = get_db()
    db.execute('delete from majors')
    db.execute('delete from programs')

    for program in programs:
        db.execute('insert into programs (code, title) values (?, ?)',
                [program.code, program.title])
        majors[program.code] = program.get_majors()

    for pcode, majorlist in majors.items():
        for major in majorlist:
            db.execute('insert into majors (code, title, pcode) values (?, ?, ?)',
                    [major.code, major.title, pcode])

    db.commit()
    print('Populated database with programs and majors')

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the current
    application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

#========================================
#========================================

def is_course_code(code):
    db = get_db()
    cur = db.execute('select code from courses where code=?', [code])
    res = cur.fetchone()

    if res is None:
        return False
    return True

def get_course_title(code):
    db = get_db()
    cur = db.execute('select title from courses where code=?', [code])
    res = cur.fetchone()
    
    if res is None:
        abort(404)

    return res['title']

def get_program(code):
    db = get_db()
    cur = db.execute('select * from programs where code=?', [code])
    res = cur.fetchone()
    if res is None:
        abort(404)
    return res

def get_major(code):
    db = get_db()
    cur = db.execute('select * from majors where code=?', [code])
    res = cur.fetchone()
    if res is None:
        abort(404)
    return res
