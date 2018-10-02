import os

from flask import json

from app import create_app, db
from app.models import Parish, Mapping

class SyncParishTask:
    def __init__(self):
        pass
    
    def save_mapping(self, mapping_json=None):
        """
        BUGFIX
        Saves a single mapping object.
        :param mapping_json:
        :return:
        """
        if mapping_json is None:
            raise Exception("Could not save mapping")
        
        mapping_obj = Mapping.from_json(mapping_json)
        saved_mapping = Mapping.query.filter_by(id=mapping_obj.id).first()
        if saved_mapping:
            db.session.merge(mapping_obj)
        else:
            db.session.add(mapping_obj)
            db.session.commit()
        
        mapping_id = saved_mapping.id if saved_mapping else mapping_obj.id
        return mapping_id
    
    def sync_parishes(self, parish_list=None):
        """
        Saves the parish payload to the database
        :param parish_list:
        :return:
        """
        results = []
        if parish_list is None:
            raise Exception("Invalid arguments")
        
        for parish in parish_list:
            print("Saving parish data")
            saved_record = Parish.query.filter_by(id=parish.get('id', None)).first()
            
            # Gets the mapping ID
            mapping_id = None
            mapping = parish.get('mapping')
            mapping_json = None
            try:
                if bool(mapping):
                    mapping_json = json.loads(mapping)
                    mapping_json = dict((k, v) for k, v in mapping_json.iteritems() if v)
            except ValueError as e:
                if len(mapping) <= 64:
                    mapping_id = mapping
            
            if mapping_json:
                mapping_id = self.save_mapping(mapping_json=mapping_json)
            
            if saved_record:
                if parish.get('id') is not None and parish.get('id') != '':
                    saved_record.id = parish.get('id')
                if parish.get('name') is not None and parish.get('name') != '':
                    saved_record.name = parish.get('name')
                if parish.get('parent') is not None and parish.get('parent') != '':
                    saved_record.parent = parish.get('parent')
                if bool(parish.get('mapping')):
                    saved_record.mapping_id = mapping_id
                if parish.get('added_by') is not None and parish.get('added_by') != '':
                    saved_record.added_by = parish.get('added_by')
                if parish.get('contact_person') is not None and parish.get('contact_person') != '':
                    saved_record.contact_person = parish.get('contact_person')
                if parish.get('phone') is not None and parish.get('phone') != '':
                    saved_record.phone = parish.get('phone')
                if parish.get('comment') is not None and parish.get('comment') != '':
                    saved_record.comment = parish.get('comment')
                if parish.get('country') is not None and parish.get('country') != '':
                    saved_record.country = parish.get('country')
                if parish.get('client_time') is not None and parish.get('client_time') != '':
                    saved_record.client_time = parish.get('client_time')
                
                db.session.merge(saved_record)
            else:
                saved_record = Parish(
                    id=parish.get('id'),
                    name=parish.get('name'),
                    parent=parish.get('parent') if parish.get('parent') != '' else None,
                    mapping_id=mapping_id,
                    added_by=parish.get('added_by') if bool(parish.get('added_by')) else None,
                    contact_person=parish.get('contact_person'),
                    phone=parish.get('phone'),
                    comment=parish.get('comment'),
                    country=parish.get('country') if bool(parish.get('country')) else None,
                    client_time=parish.get('client_time'),
                )
                db.session.add(saved_record)
            results.append(saved_record.to_json())
        db.session.commit()
        
        return results
    
    def run(self, parish_list=None):
        if parish_list is None:
            return []
        
        return self.sync_parishes(parish_list=parish_list)
