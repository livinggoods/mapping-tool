import os

from app import create_app, db
from app.models import Village

application = create_app(os.getenv('FLASK_CONFIG', 'default'))


class SyncVillagesTask:
    def __init__(self, job=None, task=None):
        if job is None or task is None:
            raise Exception("Invalid state")
        
        self.job = job
        self.task = task
    
    def sync_villages(self, village_list=None):
        """
        Sync a list of villages
        :param village_list:
        :return:
        """
        
        if village_list is None:
            raise Exception("Invalid arguments")
        
        for village in village_list:
            saved_record = Village.query.filter(Village.id == village.get('id')).first()
            if saved_record:
                # update
                saved_record.id = village.get('id')
                saved_record.village_name = village.get('village_name')
                saved_record.mapping_id = village.get('mapping_id')
                saved_record.lat = village.get('lat')
                saved_record.lon = village.get('lon')
                saved_record.country = village.get('country')
                saved_record.district = village.get('district')
                saved_record.county = village.get('county')
                saved_record.sub_county_id = village.get('sub_county_id')
                saved_record.parish_id = village.get('parish')
                saved_record.community_unit_id = village.get('community_unit') if village.get(
                    'community_unit') != "" else None
                saved_record.ward = village.get('ward')
                saved_record.link_facility_id = village.get('link_facility_id') if village.get(
                    'link_facility_id') != "" else None
                saved_record.area_chief_name = village.get('area_chief_name')
                saved_record.area_chief_phone = village.get('area_chief_phone')
                saved_record.distancetobranch = village.get('distancetobranch')
                saved_record.transportcost = village.get('transportcost')
                saved_record.distancetomainroad = village.get('distancetomainroad')
                saved_record.noofhouseholds = village.get('noofhouseholds')
                saved_record.mohpoplationdensity = village.get('mohpoplationdensity')
                saved_record.estimatedpopulationdensity = village.get('estimatedpopulationdensity')
                saved_record.economic_status = village.get('economic_status')
                saved_record.distancetonearesthealthfacility = village.get('distancetonearesthealthfacility')
                saved_record.actlevels = village.get('actlevels')
                saved_record.actprice = village.get('actprice')
                saved_record.mrdtlevels = village.get('mrdtlevels')
                saved_record.mrdtprice = village.get('mrdtprice')
                saved_record.presenceofhostels = village.get('presenceofhostels')
                saved_record.presenceofestates = village.get('presenceofestates')
                saved_record.number_of_factories = village.get('number_of_factories')
                saved_record.presenceofdistibutors = village.get('presenceofdistibutors')
                saved_record.name_of_distibutors = village.get('name_of_distibutors')
                saved_record.tradermarket = village.get('tradermarket')
                saved_record.largesupermarket = village.get('largesupermarket')
                saved_record.ngosgivingfreedrugs = village.get('ngosgivingfreedrugs')
                saved_record.ngodoingiccm = village.get('ngodoingiccm')
                saved_record.ngodoingmhealth = village.get('ngodoingmhealth')
                saved_record.nameofngodoingiccm = village.get('nameofngodoingiccm')
                saved_record.nameofngodoingmhealth = village.get('nameofngodoingmhealth')
                saved_record.privatefacilityforact = village.get('privatefacilityforact')
                saved_record.privatefacilityformrdt = village.get('privatefacilityformrdt')
                saved_record.synced = village.get('synced')
                saved_record.chvs_trained = village.get('chvs_trained')
                saved_record.client_time = village.get('dateadded')
                saved_record.addedby = village.get('addedby')
                saved_record.comment = village.get('comment')
                saved_record.brac_operating = village.get('brac_operating')
                saved_record.mtn_signal = village.get('mtn_signal')
                saved_record.safaricom_signal = village.get('safaricom_signal')
                saved_record.airtel_signal = village.get('airtel_signal')
                saved_record.orange_signal = village.get('orange_signal')
                saved_record.act_stock = village.get('act_stock')
                operation = 'updated'
            else:
                saved_record = Village(
                    id=village.get('id'),
                    village_name=village.get('village_name'),
                    mapping_id=village.get('mapping_id'),
                    lat=village.get('lat'),
                    lon=village.get('lon'),
                    country=village.get('country'),
                    district=village.get('district'),
                    county=village.get('county'),
                    sub_county_id=village.get('sub_county_id'),
                    parish_id=village.get('parish'),
                    community_unit_id=village.get('community_unit') if village.get(
                        'community_unit') != "" else None,
                    ward=village.get('ward'),
                    link_facility_id=village.get('link_facility_id') if village.get(
                        'link_facility_id') != "" else None,
                    area_chief_name=village.get('area_chief_name'),
                    area_chief_phone=village.get('area_chief_phone'),
                    distancetobranch=village.get('distancetobranch'),
                    transportcost=village.get('transportcost'),
                    distancetomainroad=village.get('distancetomainroad'),
                    noofhouseholds=village.get('noofhouseholds'),
                    mohpoplationdensity=village.get('mohpoplationdensity'),
                    estimatedpopulationdensity=village.get('estimatedpopulationdensity'),
                    economic_status=village.get('economic_status'),
                    distancetonearesthealthfacility=village.get('distancetonearesthealthfacility'),
                    actlevels=village.get('actlevels'),
                    actprice=village.get('actprice'),
                    mrdtlevels=village.get('mrdtlevels'),
                    mrdtprice=village.get('mrdtprice'),
                    presenceofhostels=village.get('presenceofhostels'),
                    presenceofestates=village.get('presenceofestates'),
                    number_of_factories=village.get('number_of_factories'),
                    presenceofdistibutors=village.get('presenceofdistibutors'),
                    name_of_distibutors=village.get('name_of_distibutors'),
                    tradermarket=village.get('tradermarket'),
                    largesupermarket=village.get('largesupermarket'),
                    ngosgivingfreedrugs=village.get('ngosgivingfreedrugs'),
                    ngodoingiccm=village.get('ngodoingiccm'),
                    ngodoingmhealth=village.get('ngodoingmhealth'),
                    nameofngodoingiccm=village.get('nameofngodoingiccm'),
                    nameofngodoingmhealth=village.get('nameofngodoingmhealth'),
                    privatefacilityforact=village.get('privatefacilityforact'),
                    privatefacilityformrdt=village.get('privatefacilityformrdt'),
                    synced=village.get('synced'),
                    chvs_trained=village.get('chvs_trained'),
                    client_time=village.get('dateadded'),
                    addedby=village.get('addedby'),
                    comment=village.get('comment'),
                    brac_operating=village.get('brac_operating'),
                    mtn_signal=village.get('mtn_signal'),
                    safaricom_signal=village.get('safaricom_signal'),
                    airtel_signal=village.get('airtel_signal'),
                    orange_signal=village.get('orange_signal'),
                    act_stock=village.get('act_stock'),
                )
                operation = 'created'
            db.session.add(saved_record)
            db.session.commit()
        
        self.task.complete = True
        db.session.add(self.task)
        db.session.commit()
    
    def run(self, village_list=None):
        if village_list is None:
            raise Exception("Invalid arguments")
        
        self.sync_villages(village_list=village_list)
