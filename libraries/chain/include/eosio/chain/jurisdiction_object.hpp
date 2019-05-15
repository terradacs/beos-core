#pragma once

#include <eosio/chain/types.hpp>

#include "multi_index_includes.hpp"

namespace eosio { namespace chain {

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

CHAINBASE_SET_INDEX_TYPE(eosio::chain::jurisdiction_object, eosio::chain::jurisdiction_index)

FC_REFLECT(eosio::chain::jurisdiction_object, (producer)(jurisdiction))
