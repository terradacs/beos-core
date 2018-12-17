import struct
import logging
import sys

MODULE_NAME = "EOSIO ABI DEF Py"
logger = logging.getLogger(MODULE_NAME)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

def pack_string(string):
  return struct.pack('I{0}s'.format(len(string)), len(string), string.encode('utf-8'))

def pack_int(integer):
  return struct.pack('I', integer)

class Abi_Type(object):
  def __init__(self, type_name, new_type):
    self.name = type_name
    self.type = new_type

  def pack(self):
    return pack_string(self.name) + pack_string(self.type)

class Abi_Field(object):
  def __init__(self, field_name, field_type):
    self.name = field_name
    self.type = field_type

  def pack(self):
    return pack_string(self.name) + pack_string(self.type)

class Abi_Struct(object):
  def __init__(self, struct_name, struct_base, struct_fields):
    self.name = struct_name
    self.base = struct_base
    self.fields = struct_fields

  def pack(self):
    packed = pack_string(self.name) + pack_string(self.base) + pack_int(len(self.fields))
    for field in self.fields:
      packed = packed + field.pack()
    return packed

class Abi_Action(object):
  def __init__(self, action_name, action_type, action_ricardian_contract):
    self.name = action_name
    self.type = action_type
    self.ricardian_contract = action_ricardian_contract

  def pack(self):
    return pack_string(self.name) + pack_string(self.type) + pack_string(self.ricardian_contract)

class Abi_Table(object):
  def __init__(self, table_name, table_index_type, table_key_names, table_key_types, table_type):
    self.name = table_name             # the name of the table
    self.index_type = table_index_type # the kind of index, i64, i128i128, etc
    self.key_names = table_key_names   # names for the keys defined by key_types
    self.key_types = table_key_types   # the type of key parameters
    self.type = table_type             # type of binary data stored in this table

  def pack(self):
    packed = pack_string(self.name) + pack_string(self.index_type) + pack_int(len(self.key_names))
    for key_name in self.key_names:
      packed = packed + pack_string(key_name)
    packed = packed + pack_int(len(self.key_types))
    for key_type in self.key_types:
      packed = packed + pack_string(key_type)
    packed = packed + pack_string(self.type)
    return packed

class Abi_Clause_Pair(object):
  def __init__(self, id, body):
    self.id = id
    self.body = body

  def pack(self):
    return pack_string(self.id) + pack_string(self.body)

class Abi_Error_Message(object):
  def __init__(self, error_code, error_message):
    self.error_code = error_code
    self.error_msg = error_message

  def pack(self):
    return pack_int(self.error_code) + pack_string(self.error_msg)

class Abi_Variant(object):
  def __init__(self, name, types):
    self.name = name
    self.types = types

  def pack(self):
    packed = pack_string(self.name) + pack_int(len(self.types))
    for tpe in self.types:
      packed = packed + tpe.pack()
    return packed

class Abi(object):
  def __init__(self, abi_as_json):
    # parsing version string
    self.version = abi_as_json.get("version", "")
    # parsing ABI types
    self.types = []
    if "types" in abi_as_json:
      for abi_type in abi_as_json["types"]:
        self.types.append(Abi_Type(abi_type["new_type_name"], abi_type["type"]))
    # parsing ABI structs
    self.structs = []
    if "structs" in abi_as_json:
      for abi_struct in abi_as_json["structs"]:
        fields = []
        for field in abi_struct["fields"]:
          fields.append(Abi_Field(field["name"], field["type"]))
        name = abi_struct["name"]
        base = abi_struct["base"]
        self.structs.append(Abi_Struct(name, base, fields))
    # parsing ABI actions
    self.actions = []
    if "actions" in abi_as_json:
      for action in abi_as_json["actions"]:
        self.actions.append(Abi_Action(action["name"], action["type"], action["ricardian_contract"]))
    # parsing ABI tables
    self.tables = []
    if "tables" in abi_as_json:
      for table in abi_as_json["tables"]:
        self.tables.append(Abi_Table(table["name"], table["index_type"], table["key_names"], table["key_types"], table["type"]))
    # parsing ABI ricardian clauses
    self.ricardian_clauses = []
    if "ricardian_clauses" in abi_as_json:
      for clause in abi_as_json["ricardian_clauses"]:
        self.ricardian_clauses.append(Abi_Clause_Pair(clause["id"], clause["body"]))
    # parsing ABI error messages
    self.error_messages = []
    if "error_messages" in abi_as_json:
      for error_message in abi_as_json["error_messages"]:
        self.error_messages.append(Abi_Error_Message(error_message["error_code"], error_message["error_message"]))
    # parsing ABI extensions
    # TODO: when needed
    self.abi_extensions = []
    if "abi_extensions" in abi_as_json:
      for abi_extension in abi_as_json["abi_extensions"]:
        raise NotImplementedError("ABI extensions not implemented yet")
    # parsing ABI variants
    # TODO: when needed
    self.variants = []
    if "variants" in abi_as_json:
      for variant in abi_as_json["variants"]:
        raise NotImplementedError("ABI variants not implemented yet")

  def pack(self):
    logger.debug("Packing ABI")
    logger.debug("Packing Version")
    packed = pack_string(self.version)

    logger.debug("Packing types")
    packed = packed + pack_int(len(self.types))
    for abi_type in self.types:
      packed = packed + abi_type.pack()
    
    logger.debug("Packing structs")
    packed = packed + pack_int(len(self.structs))
    for abi_struct in self.structs:
      packed = packed + abi_struct.pack()

    logger.debug("Packing actions")
    packed = packed + pack_int(len(self.actions))
    for abi_action in self.actions:
      packed = packed + abi_action.pack()

    logger.debug("Packing tables")
    packed = packed + pack_int(len(self.tables))
    for abi_table in self.tables:
      packed = packed + abi_table.pack()

    logger.debug("Packing ricardian clauses")
    packed = packed + pack_int(len(self.ricardian_clauses))
    for abi_ricardian_clause in self.ricardian_clauses:
      packed = packed + abi_ricardian_clause.pack()

    logger.debug("Packing error messages")
    packed = packed + pack_int(len(self.error_messages))
    for abi_error_message in self.error_messages:
      packed = packed + abi_error_message.pack()

    logger.debug("Packing abi extensions")
    packed = packed + pack_int(len(self.abi_extensions))
    for abi_extension in self.abi_extensions:
      packed = packed + abi_extension.pack()

    logger.debug("Packing variants")
    packed = packed + pack_int(len(self.variants))
    for abi_variant in self.variants:
      packed = packed + abi_variant.pack()
    return packed

  def to_dict(self):
    abi_def_dic = {
      "version" : self.version,
      "types" : self.types,
      "structs" : self.structs,
      "actions" : self.actions,
      "tables" : self.tables,
      "ricardian_clauses" : self.ricardian_clauses,
      "error_messages" : self.error_messages,
      "abi_extensions" : self.abi_extensions,
      "variants" : self.variants
    }
    return abi_def_dic
