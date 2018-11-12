/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#include <eosio/beos_plugin/beos_plugin.hpp>
#include <eosio/chain/transaction.hpp>
#include <eosio/chain/contract_types.hpp>
#include <eosio/chain/account_object.hpp>

#include <fc/io/json.hpp>
#include <boost/filesystem.hpp>

namespace eosio {

static appbase::abstract_plugin& _beos_plugin = app().register_plugin<beos_plugin>();

class beos_plugin_impl
{
  public:

    chain_plugin* chain_plug = nullptr;
};

beos_plugin::beos_plugin()
            :my( new beos_plugin_impl() )
{
}

beos_plugin::~beos_plugin()
{
}

void beos_plugin::set_program_options(options_description& cli, options_description& cfg)
{
}

void beos_plugin::plugin_initialize(const variables_map& options)
{
  my->chain_plug = app().find_plugin<chain_plugin>();
}

void beos_plugin::plugin_startup()
{
}

void beos_plugin::plugin_shutdown()
{
}

beos_apis::read_write beos_plugin::get_read_write_api() const
{
  controller& c = my->chain_plug->chain();
  return beos_apis::read_write( c, my->chain_plug->get_abi_serializer_max_time() );
}

namespace beos_apis
{
 
  read_write::address_validator_results read_write::address_validator( const address_validator_params& _account_name )
  {
    using namespace eosio::chain;
    try {
      const auto* user = db.db().find<account_object,by_name>(_account_name.account_name);
      if (user != nullptr) {
        return address_validator_results( true );
      } else {
        return address_validator_results( false );
      }
    } catch(...){

    }
    return address_validator_results( false );
  }

}

} // namespace eosio
