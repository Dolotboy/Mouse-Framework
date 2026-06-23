class Migration:
    def up(self, db):
        def table(t):
            t.increments('id')
            t.string('name')
            t.string('email').unique()
            t.string('password')
            t.timestamp('created_at').default('CURRENT_TIMESTAMP')

        db.table('users', table)

    def down(self, db):
        db.schema.drop_table('users')
