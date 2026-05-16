import bcrypt

def get_password_hash(password: str):
    # Password ko bytes mein badlein
    pwd_bytes = password.encode('utf-8')
    # Salt generate karein aur hash banayein
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    # Wapas string mein badal kar return karein
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    # Dono ko bytes mein badal kar check karein
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )
