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

class jurisdiction_producer_object : public chainbase::object<jurisdiction_producer_object_type, jurisdiction_producer_object> {
   OBJECT_CTOR(jurisdiction_producer_object)

   id_type              id;
   account_name         producer;
   code_jurisdiction    jurisdiction;

   fc::mutable_variant_object convert_to_public_jurisdiction_producer_info() const
   {
      return fc::mutable_variant_object()
         ("producer", producer)
         ("jurisdiction", jurisdiction);
   }
};

struct by_producer_jurisdiction;

using jurisdiction_producer_index = chainbase::shared_multi_index_container<
   jurisdiction_producer_object,
   indexed_by<
      ordered_unique<tag<by_id>, member<jurisdiction_producer_object, jurisdiction_producer_object::id_type, &jurisdiction_producer_object::id>>,
      ordered_unique<tag<by_producer_jurisdiction>,
         composite_key<jurisdiction_producer_object,
            member<jurisdiction_producer_object, account_name, &jurisdiction_producer_object::producer>,
            member<jurisdiction_producer_object, code_jurisdiction, &jurisdiction_producer_object::jurisdiction>
         >
      >
   >
>;

} } // eosio::chain

CHAINBASE_SET_INDEX_TYPE(eosio::chain::jurisdiction_dictionary_object, eosio::chain::jurisdiction_dictionary_index)
CHAINBASE_SET_INDEX_TYPE(eosio::chain::jurisdiction_producer_object, eosio::chain::jurisdiction_producer_index)

FC_REFLECT(eosio::chain::jurisdiction_dictionary_object, (code)(name)(description))
FC_REFLECT(eosio::chain::jurisdiction_producer_object, (producer)(jurisdiction))
