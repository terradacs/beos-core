#pragma once

#include <eosio/chain/types.hpp>
#include <fc/variant_object.hpp>

#include "multi_index_includes.hpp"

namespace eosio { namespace chain {

class jurisdiction_dictionary_object : public chainbase::object<jurisdiction_dictionary_object_type, jurisdiction_dictionary_object> {
   OBJECT_CTOR(jurisdiction_dictionary_object)

   id_type              id;
   code_jurisdiction    code;
   std::string          name;
   std::string          description;

   fc::mutable_variant_object convert_to_public_jurisdiction_dictionary_info() const
   {
      return fc::mutable_variant_object()
         ("code", code)
         ("name", name)
         ("description", description);
   }
};

struct by_code_jurisdiction_dictionary;
struct by_name_jurisdiction_dictionary;

using jurisdiction_dictionary_index = chainbase::shared_multi_index_container<
   jurisdiction_dictionary_object,
   indexed_by<
      ordered_unique<tag<by_id>, member<jurisdiction_dictionary_object, jurisdiction_dictionary_object::id_type, &jurisdiction_dictionary_object::id>>,
      ordered_unique<tag<by_code_jurisdiction_dictionary>, member<jurisdiction_dictionary_object, code_jurisdiction, &jurisdiction_dictionary_object::code>>,
      ordered_unique<tag<by_name_jurisdiction_dictionary>, member<jurisdiction_dictionary_object, std::string, &jurisdiction_dictionary_object::name>>
   >
>;

class jurisdiction_object : public chainbase::object<jurisdiction_object_type, jurisdiction_object> {
   OBJECT_CTOR(jurisdiction_object)

   id_type              id;
   account_name         producer;
   code_jurisdiction    jurisdiction;
};

struct by_producer_jurisdiction;

using jurisdiction_index = chainbase::shared_multi_index_container<
   jurisdiction_object,
   indexed_by<
      ordered_unique<tag<by_id>, member<jurisdiction_object, jurisdiction_object::id_type, &jurisdiction_object::id>>,
      ordered_unique<tag<by_producer_jurisdiction>,
         composite_key<jurisdiction_object,
            member<jurisdiction_object, account_name, &jurisdiction_object::producer>,
            member<jurisdiction_object, code_jurisdiction, &jurisdiction_object::jurisdiction>
         >
      >
   >
>;

} } // eosio::chain

CHAINBASE_SET_INDEX_TYPE(eosio::chain::jurisdiction_dictionary_object, eosio::chain::jurisdiction_dictionary_index)
CHAINBASE_SET_INDEX_TYPE(eosio::chain::jurisdiction_object, eosio::chain::jurisdiction_index)

FC_REFLECT(eosio::chain::jurisdiction_dictionary_object, (code)(name)(description))
FC_REFLECT(eosio::chain::jurisdiction_object, (producer)(jurisdiction))
