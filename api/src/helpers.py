import uuid


def generate_random_folder():
    return str(uuid.uuid4().hex)
