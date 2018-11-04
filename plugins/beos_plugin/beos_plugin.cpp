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
    std::string beos_config_file;
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
  cfg.add_options()("beos-config-file", bpo::value<string>()->default_value("beos.config.ini"), "Configuration file for BEOS" );
}

void beos_plugin::plugin_initialize(const variables_map& options)
{
  /*
    BEOS-config-file contains 2 private keys:
    - `beos.token-key` private key for account `beos.token`. This account is owner of `eosio.interchain` contract.
    - `eosio-key` private key for account `eosio`. This is system built-in account.

    Example of such file:

    {
      "beos.token-key" : "5JpSDcXq6TfzQxkFmYFXQygHR6jG3pWjtGnRmtHQd7YmCxoqLtU",
      "eosio-key" : "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
    }
  */
  if( options.count("beos-config-file") )
  {
    bfs::path file = options.at( "beos-config-file" ).as<string>();
    if( file.is_relative() )
      file = boost::filesystem::current_path() / file;

    my->beos_config_file = file.string();
  }

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

  //Retrieving private keys from BEOS config file.
  try
  {
    if( !boost::filesystem::exists( my->beos_config_file ) )
      return beos_apis::read_write( c, my->chain_plug->get_abi_serializer_max_time() );

    auto v = fc::json::from_file( my->beos_config_file );

    if( v.is_object() )
    {
      auto vo = v.get_object();

      std::string beos_token_key = vo[ "beos.token-key" ].get_string();
      std::string eosio_key = vo[ "eosio-key" ].get_string();

      return beos_apis::read_write( c, my->chain_plug->get_abi_serializer_max_time(), beos_token_key, eosio_key );
    }
    else
      return beos_apis::read_write( c, my->chain_plug->get_abi_serializer_max_time() );
  }
  catch( const fc::exception& e )
  {
    wdump((e.to_detail_string()));
  }

  return beos_apis::read_write( c, my->chain_plug->get_abi_serializer_max_time() );
}

namespace beos_apis
{

  //Preparing of action `act`.
  void read_write::create_any_action( chain::action& act, account_name account_contract, const std::string& action, fc::variant& act_data, vector< chain::permission_level >&& permissions )
  {
    act.account = account_contract;
    act.name = chain::string_to_name( action.c_str() );
    act.authorization = std::move( permissions );

    const auto& acnt = db.get_account( act.account );
    auto abi = acnt.get_abi();
    chain::abi_serializer abis( abi, abi_serializer_max_time );
    act.data = abis.variant_to_binary( action, act_data, abi_serializer_max_time );

    auto action_type = abis.get_action_type( action );
    FC_ASSERT( !action_type.empty(), "Unknown action ${action}", ("action", action) );
  }

  //Preparing `newaccount` action.
  void read_write::create_newaccount_action( chain::action& act, const transfer_params& params, chain::public_key_type&& owner_key )
  {
    chain::public_key_type active_key( params.active_key );

    auto owner_auth = chain::authority{ 1, { { owner_key, 1}}, {} };
    auto active_auth = chain::authority{ 1, { {active_key, 1}}, {} };

    chain::action act2(
                        vector<chain::permission_level>{ { params.creator, "active" } },
                        chain::newaccount{ params.creator, params.account, owner_auth, active_auth }
                      );

    act = act2;
  }

  //Preparing `buyram` action.
  void read_write::create_buy_action( chain::action& act, const transfer_params& params )
  {
    fc::variant act_data = fc::mutable_variant_object()
          ("payer", params.creator )
          ("receiver", params.account )
          ("quant", asset::from_string( params.ram ) );

    create_any_action( act, N(eosio), "buyram", act_data, { { chain::config::system_account_name, chain::config::active_name } } );
  }

  //Preparing `lock` action.
  void read_write::create_lock_action( chain::action& act, const transfer_params& params )
  {
    fc::variant act_data = fc::mutable_variant_object()
          ("from", params.from )
          ("to", params.account )
          ("quantity", asset::from_string( params.quantity ) );

    account_name acc = chain::string_to_name( params.account_contract.c_str() );
    create_any_action( act, acc, params.action, act_data, { { acc, chain::config::active_name } } );
  }

  read_write::transfer_results read_write::push_transaction( std::vector< chain::action >&& actions, std::vector< chain::private_key_type >&& keys )
  {
    //All actions are put inside 1 transaction.
    chain::signed_transaction trx;
    
    trx.actions = std::move( actions );

    trx.set_reference_block( db.head_block_id() );
    trx.expiration = db.pending_block_time() + fc::microseconds(999'999);

    for( auto& item : keys )
      trx.sign( item, db.get_chain_id() );

    auto _trx = std::make_shared< chain::transaction_metadata >( trx );
    chain::transaction_trace_ptr trace = db.push_transaction( _trx, fc::time_point::maximum() );

    transfer_results res;

    if( trace && trace->except )
    {
      edump((*trace));
      res.status = FAIL_STATUS;
    }

    /*
      There are only 2 possible responses:
      {'status': 'OK'}
      {'status': 'FAILED'}
    */
    return res;
  }

  read_write::transfer_results read_write::transfer( const read_write::transfer_params& params )
  {
    try
    {
      chain::action lock_act;
      create_lock_action( lock_act, params );

      chain::private_key_type key2 = chain::private_key_type( beos_token_key );

      //If `params.create_account` == true, then creating account is necessary.
      if( params.create_account )
      {
        //Checking if owner key matches to eosio_key from file.
        chain::private_key_type key1 = chain::private_key_type( eosio_key );
        chain::public_key_type owner_key( params.owner_key );
        if( key1.get_public_key() != owner_key )
          return transfer_results( false );

        //Account creating.
        chain::action newaccount_act;
        create_newaccount_action( newaccount_act, params, std::move( owner_key ) );

        //RAM buying. Amount of RAM is given from request.
        chain::action buyram_act;
        create_buy_action( buyram_act, params );

        return push_transaction( { newaccount_act, buyram_act, lock_act }, { key1, key2 }  );
      }
      else
      {
        return push_transaction( { lock_act }, { key2 }  );
      }
    }
    catch(...)
    {
    }

    return transfer_results( false );
  }
 
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
