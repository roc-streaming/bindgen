
def to_pascal_case(name):
    return ''.join(x.capitalize() for x in name.split('_'))


def to_camel_case(name):
    return name[0].lower() + to_pascal_case(name)[1:]
