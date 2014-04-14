# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'MenuItem.object_id'
        db.alter_column(u'menu_menuitem', 'object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True))

        # Changing field 'MenuItem.content_type'
        db.alter_column(u'menu_menuitem', 'content_type_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'MenuItem.object_id'
        raise RuntimeError("Cannot reverse this migration. 'MenuItem.object_id' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'MenuItem.object_id'
        db.alter_column(u'menu_menuitem', 'object_id', self.gf('django.db.models.fields.PositiveIntegerField')())

        # User chose to not deal with backwards NULL issues for 'MenuItem.content_type'
        raise RuntimeError("Cannot reverse this migration. 'MenuItem.content_type' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'MenuItem.content_type'
        db.alter_column(u'menu_menuitem', 'content_type_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType']))

    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'menu.menugroup': {
            'Meta': {'ordering': "('name',)", 'object_name': 'MenuGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'menu.menuitem': {
            'Meta': {'ordering': "('position',)", 'object_name': 'MenuItem'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'css_class': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['menu.MenuGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['menu.MenuItem']"}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '1000'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['menu']