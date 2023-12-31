import logging,random
from host_app.database.schemas import ServiceSignup
from host_app.database.models import Service
from sqlalchemy.orm import Session
from host_app.common import util
from host_app.routes import verification



def get_service_by_service_id(db: Session, service_id: str):
    try:
        service_obj = db.query(Service).filter(Service.service_id==service_id).first()
        return service_obj.to_dict() if service_obj else None
    except Exception as ex :
        logging.exception("[SERVICE_CRUD][Exception in get_service_by_service_id] {} ".format(ex))


def get_service_by_api_key(db: Session, api_key: str) -> dict:
    try:
        service_obj = db.query(Service).filter(Service.api_key==api_key).first()
        return service_obj.to_dict() if service_obj else None
    
    except Exception as ex :
        logging.exception("[SERVICE_CRUD][Exception in get_service_by_api_key] {} ".format(ex))



def get_service_by_email(db: Session, email: str):
    try:
        service_obj = db.query(Service).filter(Service.registration_mail == email).first()
        return service_obj.to_dict() if service_obj else None
    except Exception as ex :
        logging.exception("[SERVICE_CRUD][Exception in get_service_by_email] {} ".format(ex))


def get_service_by_service_org(db: Session, service_org: str):
    try:
        service_obj = db.query(Service).filter(Service.service_org == service_org).first()
        return service_obj.to_dict() if service_obj else None
    except Exception as ex :
        logging.exception("[SERVICE_CRUD][Exception in get_service_by_service_org] {} ".format(ex))



async def create_new_service(db: Session, service_user: ServiceSignup):
    try:
        ip_ports = service_user.ip_ports
        ip_ports_str = await util.zipper(ip_ports)
        service_org = service_user.service_org
        alpha_int = random.randint(1,26)

        service_id = service_org + "_" + chr(64 + alpha_int) + str(random.randint(1,999))
        
        api_key = await verification.get_api_key()
        
        subscription_mode = service_user.subscription_mode
        if subscription_mode :
            daily_request_count = Service.get_request_count(subscription_mode)
            db_user = Service(service_org=service_org, service_id=service_id, service_name = service_user.service_name, registration_mail=service_user.registration_mail, ip_ports=ip_ports_str, api_key=api_key, subscription_mode=subscription_mode, daily_request_count=daily_request_count )
        
        else:
            db_user = Service(service_org=service_org, service_id=service_id, service_name = service_user.service_name, registration_mail=service_user.registration_mail, ip_ports=ip_ports_str, api_key=api_key)
            
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        enc_api_key = await verification.get_encrypted_api_key(api_key)

        response = await ServiceSignupResponse(db_user, enc_api_key)
        return response

    except Exception as ex :
        logging.exception("[SERVICE_CRUD][Exception in create_new_service] {} ".format(ex))
    return None



async def update_service_data(db: Session, service_id: int, service_update_map: dict):
    try :
        db_user = db.query(Service).filter(Service.service_id == service_id).first()
        if db_user:
            for key, value in service_update_map.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
            return db_user
        return None
    except Exception as ex :
        logging.exception("[SERVICE_CRUD][Exception in update_service_data] {} ".format(ex))




async def ServiceSignupResponse(data: Service, enc_api_key):
    # Your processing logic here
    return {
        "service_name": data.service_name,
        "service_org": data.service_org,
        "service_id": data.service_id,
        "enc_api_key": enc_api_key,
        "subscription_mode": data.subscription_mode,
        "daily_request_count": data.daily_request_count
    }
    
    
