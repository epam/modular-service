def from_json(cls, model_json):
    if not model_json:
        return cls()
    attributes = cls.get_attributes()
    attributes_values = {}
    for key, attribute_inst in attributes.items():
        attributes_values[key] = model_json.get(attribute_inst.attr_name)
    class_item = cls(**attributes_values)
    class_item.mongo_id = model_json.get('_id')
    return class_item