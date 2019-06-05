#pragma once
#include <eosio/chain/jurisdiction_object.hpp>

namespace eosio 
{
  namespace chain
  {
    class jurisdiction_history_object : public chainbase::object<chain::jurisdiction_history_object_type, jurisdiction_history_object> 
    {
      OBJECT_CTOR(jurisdiction_history_object)

      id_type id;
      chain::account_name producer_name;
      uint64_t block_number;
      fc::time_point date_changed;
      std::vector<chain::code_jurisdiction> new_jurisdictions;
    };

    struct by_producer_name;
    struct by_producer_block_number;
    struct by_block_number;
    struct by_date_changed;

    using jurisdiction_history_index = chainbase::shared_multi_index_container<
      jurisdiction_history_object,
      bmi::indexed_by<
        bmi::ordered_unique<
          bmi::tag<by_id>, 
          bmi::member<jurisdiction_history_object, jurisdiction_history_object::id_type, &jurisdiction_history_object::id>
        >,
        bmi::ordered_non_unique<
          bmi::tag<by_producer_name>, 
          bmi::member<jurisdiction_history_object, chain::account_name, &jurisdiction_history_object::producer_name>
        >,
        bmi::ordered_unique<
          bmi::tag<by_producer_block_number>,
          bmi::composite_key<
            jurisdiction_history_object,
            bmi::member<jurisdiction_history_object, chain::account_name, &jurisdiction_history_object::producer_name>,
            bmi::member<jurisdiction_history_object, uint64_t, &jurisdiction_history_object::block_number>
          >
        >,
        bmi::ordered_non_unique<
          bmi::tag<by_block_number>, 
          bmi::member<jurisdiction_history_object, uint64_t, &jurisdiction_history_object::block_number>
        >,
        bmi::ordered_non_unique<
          bmi::tag<by_date_changed>, 
          bmi::member<jurisdiction_history_object, fc::time_point, &jurisdiction_history_object::date_changed>
        >
      >
    >;
  }
}

CHAINBASE_SET_INDEX_TYPE(eosio::chain::jurisdiction_history_object, eosio::chain::jurisdiction_history_index)
FC_REFLECT(eosio::chain::jurisdiction_history_object, (producer_name)(block_number)(date_changed)(new_jurisdictions))