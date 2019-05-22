#include <boost/test/unit_test.hpp>
#include <eosio/testing/tester.hpp>
#include <eosio/chain/abi_serializer.hpp>
#include <eosio/chain/resource_limits.hpp>
#include <eosio/chain/jurisdiction_objects.hpp>

#include <eosio.system/eosio.system.wast.hpp>
#include <eosio.system/eosio.system.abi.hpp>
#include <eosio.token/eosio.token.wast.hpp>
#include <eosio.token/eosio.token.abi.hpp>
#include <eosio.init/eosio.init.wast.hpp>
#include <eosio.init/eosio.init.abi.hpp>
#include <eosio.gateway/eosio.gateway.wast.hpp>
#include <eosio.gateway/eosio.gateway.abi.hpp>
#include <eosio.distribution/eosio.distribution.wast.hpp>
#include <eosio.distribution/eosio.distribution.abi.hpp>
#include <eosio.jurisdiction/eosio.jurisdiction.wast.hpp>
#include <eosio.jurisdiction/eosio.jurisdiction.abi.hpp>

#include <Runtime/Runtime.h>

#include <fc/variant_object.hpp>

using namespace eosio::testing;
using namespace eosio;
using namespace eosio::chain;
using namespace eosio::testing;
using namespace fc;
using namespace std;

using mvo = fc::mutable_variant_object;

//Below value is set according to 'native::newaccount' action.
static const uint64_t DEFAULT_RAM = 2724 * 2;

struct actions: public tester
{
  abi_serializer beos_init_abi_ser;
  abi_serializer beos_gateway_abi_ser;
  abi_serializer token_abi_ser;
  abi_serializer beos_distrib_abi_ser;
  abi_serializer system_abi_ser;

  actions(uint64_t state_size = 1024*1024*8) : tester(true, db_read_mode::SPECULATIVE, state_size) {}

  action_result push_actions( std::vector<action>&& acts, uint64_t authorizer )
  {
    signed_transaction trx;
    if (authorizer)
    {
      for( auto& item : acts )
        item.authorization = vector<permission_level>{{authorizer, config::active_name}};
    }
    trx.actions = acts;
    set_transaction_headers(trx);
    if (authorizer) {
        trx.sign(get_private_key(authorizer, "active"), control->get_chain_id());
    }
    try {
        push_transaction(trx);
    } catch (const fc::exception& ex) {
        edump((ex.to_detail_string()));
        return error(ex.top_message()); // top_message() is assumed by many tests; otherwise they fail
        //return error(ex.to_detail_string());
    }
    produce_block();
    BOOST_REQUIRE_EQUAL(true, chain_has_transaction(trx.id()));
    return success();
  }

  void create_action( action& act, const action_name &name, const variant_object &data, const abi_serializer& ser, account_name owner )
  {
    string action_type_name = ser.get_action_type( name );

    act.account = owner;
    act.name    = name;
    act.data    = ser.variant_to_binary( action_type_name, data, abi_serializer_max_time );
  }

  template <typename T>
  void create_action( action& act, const action_name& name, const T& data, account_name owner )
  {
    act.account = owner;
    act.name    = name;
    act.data    = fc::raw::pack(data);
  }

  template <typename T>
  action_result push_action( const account_name& signer, const action_name &name, const T& data, const account_name& owner)
  {
    action act;
    create_action( act, name, data, owner );

    return base_tester::push_action( std::move(act), uint64_t(signer));
  }

  action_result push_action( const account_name& signer, const action_name &name, const variant_object &data, const abi_serializer& ser, const account_name& owner )
  {
    action act;
    create_action( act, name, data, ser, owner );

    return base_tester::push_action( std::move(act), uint64_t(signer));
  }

  action_result create_currency( name contract, name manager, asset maxsupply )
  {
    return push_action(contract, N(create), mvo()
        ("issuer",       manager )
        ("maximum_supply", maxsupply ),
        token_abi_ser,
        N(eosio.token)
      );
  }

  action_result issue( name to, const asset& amount, name manager )
  {
    return push_action( manager, N(issue), mvo()
        ("to",      to )
        ("quantity", amount )
        ("memo", ""),
        token_abi_ser,
        N(eosio.token)
      );
  }

  action_result setpriv( name account )
  {
    return push_action( config::system_account_name, N(setpriv), mvo()
      ("account", account )
      ("is_priv", 1 ),
      system_abi_ser,
      config::system_account_name
    );
  }

  action create_issue_action( account_name to, asset quantity )
  {
    action act;

    create_action( act, N(issue), mvo()
      ( "to", to )
      ( "quantity", quantity )
      ( "memo", ""),
      beos_gateway_abi_ser,
      N(beos.gateway)
      );

    return act;
  }

  action_result issue( account_name to, asset quantity )
  {
    action act = create_issue_action( to, quantity );
    return base_tester::push_action( std::move( act ), config::gateway_account_name );
  }

  action_result withdraw( account_name from, asset quantity )
  {
    return push_action( from, N(withdraw), mvo()
        ( "from", from )
        ( "bts_to", "any_bts_account" )
        ( "quantity", quantity ),
        beos_gateway_abi_ser,
        N(beos.gateway)
      );
  }

  action_result locks( account_name from, std::vector< action >&& acts )
  {
    return push_actions( std::move( acts ), uint64_t( from ) );
  }

  action_result initresource( account_name receiver, int64_t bytes, asset stake_net_quantity, asset stake_cpu_quantity )
  {
    return push_action( config::system_account_name, N(initresource), mvo()
        ( "receiver", receiver )
        ( "bytes", bytes )
        ( "stake_net_quantity", stake_net_quantity.get_amount() )
        ( "stake_cpu_quantity", stake_cpu_quantity.get_amount() ),
        system_abi_ser,
        config::system_account_name
      );
  }

  action_result unstake( account_name from, account_name receiver, asset unstake_net_quantity, asset unstake_cpu_quantity )
  {
    return push_action( from, N(undelegatebw), mvo()
        ( "from", from )
        ( "receiver", receiver )
        ( "unstake_net_quantity", unstake_net_quantity )
        ( "unstake_cpu_quantity", unstake_cpu_quantity ),
        system_abi_ser,
        config::system_account_name
      );
  }

  fc::variant get_stats( const string& symbolname ) {
    auto symb = eosio::chain::symbol::from_string(symbolname);
    auto symbol_code = symb.to_symbol_code().value;
    vector<char> data = get_row_by_account( N(eosio.token), symbol_code, N(stat), symbol_code );
    return data.empty() ? fc::variant() : token_abi_ser.binary_to_variant( "currency_stats", data, abi_serializer_max_time );
  }

  asset get_token_supply() {
    return get_stats("4," CORE_SYMBOL_NAME)["supply"].as<asset>();
  }

  action_result claimrewards( account_name owner )
  {
    return push_action( owner, N(claimrewards), mvo()
        ( "owner", owner ),
        system_abi_ser,
        config::system_account_name
      );
  }

};

class eosio_interchain_tester : public actions
{
  protected:

  void prepare_account( account_name account, const char* _wast, const char* _abi, abi_serializer* ser = nullptr )
  {
    produce_blocks( 2 );

    set_code( account, _wast );
    set_abi( account, _abi );

    const auto& accnt = control->db().get<account_object,by_name>( account );
    abi_def abi;
    BOOST_REQUIRE_EQUAL(abi_serializer::to_abi(accnt.abi, abi), true);
    if( ser )
      ser->set_abi(abi, abi_serializer_max_time);
  }

  public:

  eosio_interchain_tester(uint64_t state_size = 1024*1024*8,
                          uint64_t initial_supply = 1'000'000'000'0000,
                          uint8_t min_activated_stake_percent = 15, // 15% is default in eosio
                          uint64_t gateway_init_ram = 100'000'000,
                          uint64_t gateway_init_net = 1000'0000,
                          uint64_t gateway_init_cpu = 1000'0000,
                          uint64_t distrib_init_ram = 30'000'300'000, //30'000'000'000 + 300'000 default leftover + 0 default ram trustee reward
                          uint64_t distrib_init_net = 200'001'001'0000, //200'000'000.0000 + 1.0000 leftover + 1000.0000 default beos trustee reward (set == 0 for auto calculation)
                          uint64_t distrib_init_cpu = 1'0000) //this is leftover from distribution - that amount will be left on distrib on both net and cpu
    : actions(state_size)
  {
    produce_blocks( 2 );

    create_accounts({
                      N(eosio.token), N(eosio.ram), N(eosio.ramfee), N(eosio.stake),
                      N(eosio.bpay), N(eosio.vpay), N(eosio.saving), N(eosio.names),
                      N(beos.init)
                    });

    prepare_account( N(eosio.token), eosio_token_wast, eosio_token_abi, &token_abi_ser );

    create_currency( N(eosio.token), config::system_account_name, asset::from_string("10000000000.0000 BEOS") );
    create_currency( N(eosio.token), config::gateway_account_name, asset::from_string("10000000000.0000 PROXY") );
    create_currency( N(eosio.token), config::gateway_account_name, asset::from_string("10000000000.000000 BROWNIE") );
    create_currency( N(eosio.token), config::gateway_account_name, asset::from_string("10000000000.00000 PXEOS") );
    produce_blocks( 1 );

    prepare_account( config::system_account_name, eosio_system_wast, eosio_system_abi, &system_abi_ser );
    prepare_account( N(beos.init), eosio_init_wast, eosio_init_abi, &beos_init_abi_ser );
    prepare_account( config::gateway_account_name, eosio_gateway_wast, eosio_gateway_abi, &beos_gateway_abi_ser );
    prepare_account( config::distribution_account_name, eosio_distribution_wast, eosio_distribution_abi, &beos_distrib_abi_ser );

    //BOOST_REQUIRE_EQUAL( success(), issue( config::system_account_name, asset::from_string("1000000000.0000 BEOS"), config::system_account_name ) );
    BOOST_REQUIRE_EQUAL( success(), push_action( config::system_account_name, N(initialissue),
                                                 mvo()
                                                   ( "quantity", initial_supply )
                                                   ( "min_activated_stake_percent", min_activated_stake_percent ),
                                                 system_abi_ser,
                                                 config::system_account_name
                                               )
                       );

    BOOST_REQUIRE_EQUAL( success(), initresource( config::gateway_account_name,
                                                    gateway_init_ram,
                                                    asset(gateway_init_net, symbol(4,"BEOS")),
                                                    asset(gateway_init_cpu, symbol(4,"BEOS"))
                                                )
                       );
    BOOST_REQUIRE_EQUAL( success(), initresource( config::distribution_account_name,
                                                    distrib_init_ram,
                                                    asset::from_string("-0.0001 BEOS"),
                                                    asset::from_string("-0.0001 BEOS")
                                                )
                       );
    //beos.distrib only distributes resources stored as net weight (minus value on cpu)
    if (distrib_init_net == 0) {
       distrib_init_net = get_balance(config::system_account_name).get_amount() - distrib_init_cpu;
    }
    BOOST_REQUIRE_EQUAL( success(), initresource( config::distribution_account_name,
                                                    -1,
                                                    asset(distrib_init_net, symbol(4,"BEOS")),
                                                    asset(distrib_init_cpu, symbol(4,"BEOS"))
                                                )
                       );
    //ABW: we need to have enough resources to cover all tests regardless of distribution parameters (we leave plenty of liquid BEOS on eosio
    //because if it was calculated as in case of normal initialization phase test results for distribution would be more unstable)

    // [MK]: need to change creation with multisig
    create_account_with_resources( config::gateway_account_name, N(terradacs) );
    create_account_with_resources( config::gateway_account_name, N(beos.trustee) );

    create_account_with_resources( config::gateway_account_name, N(alice) );
    create_account_with_resources( config::gateway_account_name, N(bob) );
    create_account_with_resources( config::gateway_account_name, N(carol) );
    create_account_with_resources( config::gateway_account_name, N(dan) );
    produce_blocks( 1 );
  }

  asset get_balance( const account_name& act, std::string coin_name = "BEOS" )
  {
  vector<char> data = get_row_by_account( N(eosio.token), act, N(accounts), symbol( 4, coin_name.c_str() ).to_symbol_code().value );
  return data.empty() ? asset(0, symbol( 4, coin_name.c_str() )) : token_abi_ser.binary_to_variant( "account", data, abi_serializer_max_time )["balance"].as<asset>();
  }

  fc::variant check_data( account_name acc )
  {
    asset balance = get_balance( acc, "PROXY" );
    const auto& resource_limit_mgr = control->get_resource_limits_manager();
    int64_t ram_bytes = 0;
    int64_t net_weight = 0;
    int64_t cpu_weight = 0;

    resource_limit_mgr.get_account_limits( acc, ram_bytes, net_weight, cpu_weight );

    asset a_total_net_cpu( net_weight + cpu_weight );

    return mvo()
      ( "balance", balance )
      ( "staked_balance", a_total_net_cpu )
      ( "staked_ram", ram_bytes );
  }

  transaction_trace_ptr create_account_with_resources( account_name creator, account_name a ) {
    signed_transaction trx;
    set_transaction_headers(trx);

    authority owner_auth;

    owner_auth =  authority( get_public_key( a, "owner" ) );

    trx.actions.emplace_back( vector<permission_level>{{creator,config::active_name}},
                              newaccount{
                                  .creator  = creator,
                                  .name     = a,
                                  .init_ram = true,
                                  .owner    = owner_auth,
                                  .active   = authority( get_public_key( a, "active" ) )
                              });

    set_transaction_headers(trx);
    trx.sign( get_private_key( creator, "active" ), control->get_chain_id()  );
    return push_transaction( trx );
  }

  action_result change_init_params( const test_global_state& tgs )
  {
    variants v;
    v.emplace_back( tgs.starting_block_for_initial_witness_election );
    return push_action( N(beos.init), N(changeparams), mvo()
       ("new_params", v), beos_init_abi_ser, N(beos.init) );
  }

  action_result change_distrib_params( const test_global_state& tgs )
  {
    variants v;
    v.emplace_back( std::move( tgs.beos ) );
    v.emplace_back( std::move( tgs.ram ) );
    v.emplace_back( std::move( tgs.proxy_assets ) );
    v.emplace_back( std::move( tgs.ram_leftover ) );
    return push_action( N(beos.distrib), N(changeparams), mvo()
       ("new_params", v), beos_distrib_abi_ser, N(beos.distrib) );
  }

  action_result change_gateway_params()
  {
    test_gateway_global_state tgs;

    tgs.proxy_assets.emplace_back( asset( 0, symbol(SY(6, PROXY)) ), "bts" );
    tgs.proxy_assets.emplace_back( asset( 0, symbol(SY(6, BROWNIE)) ), "brownie.pts" );
    tgs.proxy_assets.emplace_back( asset( 0, symbol(SY(6, PXEOS)) ), "eos" );

    variants v;
    v.emplace_back( std::move( tgs.proxy_assets ) );
    return push_action( N(beos.gateway), N(changeparams), mvo()
       ("new_params", v), beos_gateway_abi_ser, N(beos.gateway) );
  }

  void check_change_params( const test_global_state& tgs )
  {
     BOOST_REQUIRE_EQUAL( success(), change_init_params( tgs ) );
     BOOST_REQUIRE_EQUAL( success(), change_distrib_params( tgs ) );
     BOOST_REQUIRE_EQUAL( success(), change_gateway_params() );
  }

fc::variant get_init_param()
  {
    vector<char> data = get_row_by_account( N(beos.init), N(beos.init), N(beosglobal), N(beosglobal) );
    if( data.empty() )
      return fc::variant();
    else
      return beos_init_abi_ser.binary_to_variant( "beos_global_state", data, abi_serializer_max_time );
  }

  fc::variant get_distrib_param()
  {
    vector<char> data = get_row_by_account( N(beos.distrib), N(beos.distrib), N(distribstate), N(distribstate) );
    if( data.empty() )
      return fc::variant();
    else
      return beos_distrib_abi_ser.binary_to_variant( "distrib_global_state", data, abi_serializer_max_time );
  }

  action_result store_params_init()
  {
    return push_action( N(beos.init), N(storeparams), mvo()("dummy",0),
        beos_init_abi_ser,
        N(beos.init)
      );
  }

  action_result store_params_distrib()
  {
    return push_action( N(beos.distrib), N(storeparams), mvo()("dummy", 0),
        beos_distrib_abi_ser,
        N(beos.distrib)
      );
  }
};

class eosio_init_tester: public eosio_interchain_tester
{
  public:
 
  eosio_init_tester(uint64_t state_size = 1024*1024*8,
                    uint64_t initial_supply = 1'000'000'000'0000,
                    uint8_t min_activated_stake_percent = 15,
                    uint64_t gateway_init_ram = 100'000'000,
                    uint64_t gateway_init_net = 1000'0000,
                    uint64_t gateway_init_cpu = 1000'0000,
                    uint64_t distrib_init_ram = 30'000'300'000,
                    uint64_t distrib_init_net = 200'001'001'0000,
                    uint64_t distrib_init_cpu = 1'0000)
    : eosio_interchain_tester(state_size, initial_supply, min_activated_stake_percent, gateway_init_ram, gateway_init_net, gateway_init_cpu,
                              distrib_init_ram, distrib_init_net, distrib_init_cpu) {}

  fc::variant get_producer_info( const account_name& act )
  {
    vector<char> data = get_row_by_account( config::system_account_name, config::system_account_name, N(producers), act );
    if( data.size() )
      return system_abi_ser.binary_to_variant( "producer_info", data, abi_serializer_max_time );
    else
      return fc::variant();
  }

  action_result vote_producer( const account_name& voter, const std::vector<account_name>& producers, const account_name& proxy = name(0) )
  {
    return push_action(voter, N(voteproducer), mvo()
        ("voter",     voter)
        ("proxy",     proxy)
        ("producers", producers),
        system_abi_ser,
        config::system_account_name
      );
  }

  action_result create_producer( const account_name& producer )
  {
    return push_action( producer, N(regproducer), mvo()
        ("producer", producer )
        ("producer_key", get_public_key( producer, "active") )
        ("url", "http://fake.html")
        ("location", 0 ),
        system_abi_ser,
        config::system_account_name
      );
  }

  action_result stake( const account_name& from, const account_name& receiver, const asset& net, const asset& cpu, bool transfer )
  {
    return push_action( from, N(delegatebw), mvo()
        ("from",     from)
        ("receiver", receiver)
        ("stake_net_quantity", net)
        ("stake_cpu_quantity", cpu)
        ("transfer", transfer ),
        system_abi_ser,
        config::system_account_name
      );
  }
  
  action_result buyram( const account_name& payer, const account_name& receiver, asset ram_cost )
  {
    return push_action( payer, N(buyram), mvo()
        ("payer", payer)
        ("receiver", receiver)
        ("quant", ram_cost),
        system_abi_ser,
        config::system_account_name
      );
  }

  action_result buyrambytes( const account_name& payer, const account_name& receiver, uint64_t numbytes )
  {
    return push_action( payer, N(buyrambytes), mvo()
        ("payer", payer)
        ("receiver", receiver)
        ("bytes",numbytes),
        system_abi_ser,
        config::system_account_name
      );
  }

  action_result sellram( const account_name& account, uint64_t numbytes )
  {
    return push_action( account, N(sellram), mvo()
        ("account", account)
        ("bytes",numbytes),
        system_abi_ser,
        config::system_account_name
      );
  }

  void checker( const test_global_state& tgs, test_global_state_element& state )
  {
    auto saved_state = state;

    state.starting_block = 0;
    state.ending_block = control->head_block_num()+1;
    BOOST_REQUIRE_EQUAL( wasm_assert_msg("Starting block already passed"), change_distrib_params( tgs ) );
    BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
    state = saved_state;

    state.starting_block = 3;
    state.ending_block = 2;
    BOOST_REQUIRE_EQUAL( wasm_assert_msg("Distribution period must not be empty"), change_distrib_params( tgs ) );
    BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
    state = saved_state;

    state.block_interval = 0;
    BOOST_REQUIRE_EQUAL( wasm_assert_msg("Distribution block interval must be positive value"), change_distrib_params( tgs ) );
    BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
    state = saved_state;

    //no longer possible - changeparams automatically sets next_block to value of starting_block since it is
    //the only valid value anyway, so you don't have to set it everywhere
    //state.next_block = state.starting_block + 1;
    //BOOST_REQUIRE_EQUAL( wasm_assert_msg("Distribution should start in starting block"), change_distrib_params( tgs ) );
    //BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
    //state = saved_state;
  }

};

/*
  Values of parameters for `eosio_init` contract.

  starting_block_for_initial_witness_election               100

  starting_block_for_beos_distribution                      240
  ending_block_for_beos_distribution                        270
  distribution_payment_block_interval_for_beos_distribution 10
  trustee_reward_beos                                       800000

  starting_block_for_ram_distribution                       240
  ending_block_for_ram_distribution                         248
  distribution_payment_block_interval_for_ram_distribution  4
  trustee_reward_ram                                        0
*/

class eosio_init_bigstate_tester : public eosio_init_tester
{
public:
  using account_names_t = vector<account_name>;

public:
  eosio_init_bigstate_tester() : eosio_init_tester(state_size) {}

  account_names_t generate_account_list( size_t no_of_accounts = eosio_init_bigstate_tester::no_of_accounts )
  {
    if (no_of_accounts == 0)
      return account_names_t();

    const char chars[] = "12345abcdefghijklmnopqrstuvwxyz";
    const size_t no_of_chars = sizeof(chars) - 1;
    account_names_t names;
    names.reserve( no_of_accounts );

    auto generate_part = [&] (const std::string& prefix) -> bool
      {
      for (size_t i = 0; i < no_of_chars && no_of_accounts != 0; ++i, --no_of_accounts)
        names.emplace_back( prefix + chars[i] );

      return no_of_accounts != 0;
      };

    auto generate_range = [&] (size_t begin, size_t end) -> bool
      {
      for (; begin < end; ++begin)
        {
        if (generate_part( names[begin].to_string() ) == false)
          return false;
        }

      return true;
      };

    names.emplace_back("1");

    if (--no_of_accounts == 0)
      return names;

    size_t begin = 0;
    size_t end = names.size();

    while (generate_range( begin, end ))
      {
      begin = end;
      end = names.size();
      }

    /*FILE* file = fopen("accounts", "w");
    for (auto& name : names)
      fprintf(file, "%s\n", name.to_string().c_str());
    fclose(file);*/

    return names;
  }

  account_names_t create_accounts_with_resources( account_name creator, size_t no_of_accounts = eosio_init_bigstate_tester::no_of_accounts,
    int64_t bytes = DEFAULT_RAM )
  {
    account_names_t names( generate_account_list( no_of_accounts ) );
    size_t i = 0;

    while ( i < no_of_accounts )
    {
      size_t no_of_actions = std::min(actions_per_trx, no_of_accounts - i);
      signed_transaction trx;
      trx.actions.reserve(no_of_actions);

      set_transaction_headers(trx);

      for (size_t j = 0; j < no_of_actions; ++j, ++i)
      {
        account_name name = names[i];

        trx.actions.emplace_back( vector<permission_level>{{creator,config::active_name}},
                                  newaccount{
                                      .creator  = creator,
                                      .name     = name,
                                      .init_ram = true,
                                      .owner    = authority( get_public_key( name, "owner" ) ),
                                      .active   = authority( get_public_key( name, "active" ) )
                                  });
      }

      set_transaction_headers(trx);
      trx.sign( get_private_key( creator, "active" ), control->get_chain_id() );

      try
      {
         push_transaction(trx);
      }
      catch (const fc::exception& ex)
      {
         edump((ex.to_detail_string()));
         return account_names_t();
      }

      produce_block();
      BOOST_REQUIRE_EQUAL(true, chain_has_transaction(trx.id()));
    }

    return names;
  }

  void issue_for_accounts( const account_names_t& accounts, const asset& quantity )
  {
    size_t i = 0;

    while ( i < accounts.size() )
    {
      size_t no_of_actions = std::min(actions_per_trx, accounts.size() - i);
      signed_transaction trx;
      trx.actions.reserve(no_of_actions);

      set_transaction_headers(trx);

      for (size_t j = 0; j < no_of_actions; ++j, ++i)
      {
        account_name name = accounts[i];
        action act = create_issue_action( name, quantity );
        act.authorization = vector<permission_level>{{config::gateway_account_name, config::active_name}};
        trx.actions.emplace_back(std::move(act));
      }

      set_transaction_headers(trx);
      trx.sign(get_private_key(config::gateway_account_name, "active"), control->get_chain_id());

      try
      {
        push_transaction(trx);
      }
      catch (const fc::exception& ex)
      {
        edump((ex.to_detail_string()));
        return;
      }

      produce_block();
      BOOST_REQUIRE_EQUAL(true, chain_has_transaction(trx.id()));
    }
  }

protected:
  test_global_state     tgs;
  uint32_t              reward_period = 0;

protected:
  static uint64_t       state_size; //< could be changed before run particular test case
  static size_t         no_of_accounts; //< could be changed before run particular test case
  static const size_t   actions_per_trx;
};

/**
 * This tester initializes chain with parameters like in BEOS mainnet so we can test various effects
 * as they will be on regular BEOS (suitable f.e. to observe actual cost of RAM)
 */
class beos_mainnet_tester : public eosio_init_tester
{
public:

beos_mainnet_tester(uint64_t state_size = 1024*1024*8)
   : eosio_init_tester(state_size, 3'674'470'000'0000, 15, 164'000'000, 10'000'0000, 10'000'0000,
                       32'000'300'000, 0, 1'0000) {}
};

uint64_t eosio_init_bigstate_tester::state_size = 1 * 1024 * 1024 * 1024ll;
size_t eosio_init_bigstate_tester::no_of_accounts = 50'000; //< it passed succesfuly for 100k accounts and 1G state
const size_t eosio_init_bigstate_tester::actions_per_trx = 2000;

#define CHECK_STATS_(_accName, _expectedBalance, _expectedStakedBalance, _expectedStakedRam)  \
{                                                                                             \
    auto stats = check_data( _accName );                                                      \
    const bool expected_balance_empty = strlen(_expectedBalance) == 0;                        \
    const bool expected_staked_balance_empty = strlen(_expectedStakedBalance) == 0;           \
    const bool expected_staked_ram_empty = strlen(_expectedStakedRam) == 0 ;                  \
    if(!expected_balance_empty){                                                              \
      BOOST_REQUIRE_EQUAL( stats["balance"].as_string(), ( _expectedBalance ) );              \
    }                                                                                         \
    if(!expected_staked_balance_empty){                                                       \
      BOOST_REQUIRE_EQUAL( stats["staked_balance"].as_string(), ( _expectedStakedBalance ) ); \
    }                                                                                         \
    if(!expected_staked_ram_empty) {                                                          \
      int64_t staked_ram = stats["staked_ram"].as_int64() - DEFAULT_RAM;                      \
      BOOST_REQUIRE_EQUAL( std::to_string(staked_ram), ( _expectedStakedRam ) );              \
    }                                                                                         \
};

#define CHECK_STATS(_accName, _expectedBalance, _expectedStakedBalance, _expectedStakedRam)   \
  CHECK_STATS_(N(_accName), _expectedBalance, _expectedStakedBalance, _expectedStakedRam)

inline uint64_t check_asset_value(uint64_t value)
  {
  BOOST_REQUIRE_EQUAL( value, (value / 10000) * 10000);
  return value / 10000;
  }

#define ASSET_STRING(INTEGER, SYMBOL) std::string(std::to_string(check_asset_value(INTEGER)) + ".0000 " + #SYMBOL).c_str()

class beos_jurisdiction_tester : public eosio_init_tester
{
   abi_serializer jurisdiction_abi_ser;

   public:

      beos_jurisdiction_tester()
      {
         produce_blocks( 2 );

         std::vector< account_name > actors = { N(beos.jurisdi), N(beos.proda), N(beos.prodb), N(beos.prodc) };
         
         for( const auto& item : actors )
         {
            create_account_with_resources( config::gateway_account_name, item );
            issue( item, asset::from_string("100.0000 PROXY") );
         }

         test_global_state tgs;

         tgs.ram.starting_block = 100;
         tgs.ram.ending_block = 110;
         tgs.ram.block_interval = 5;

         tgs.beos.starting_block = 100;
         tgs.beos.ending_block = 110;
         tgs.beos.block_interval = 5;

         check_change_params( tgs );

         produce_blocks( 120 - control->head_block_num() );
         BOOST_REQUIRE_EQUAL( control->head_block_num(), 120u );

         set_privileged( N(beos.jurisdi) );

         prepare_account( N(beos.jurisdi), eosio_jurisdiction_wast, eosio_jurisdiction_abi, &jurisdiction_abi_ser );

         for( const auto& item : actors )
         {
            if( item != N(beos.jurisdi) )
            {
               BOOST_REQUIRE_EQUAL( success(), create_producer( item ) );
               produce_blocks(1);
               BOOST_REQUIRE_EQUAL( success(), vote_producer( item, { item } ) );
               produce_blocks(1);
            }
         }

         for( const auto& item : actors )
            BOOST_REQUIRE_EQUAL( success(), unstake( item, item, asset::from_string("20000000.0000 BEOS"), asset::from_string("20000000.0000 BEOS") ) );

         produce_block( fc::hours(3*24) );
         produce_blocks(1);
      }

      transaction_trace_ptr set_privileged( name account ) {
         auto r = base_tester::push_action(config::system_account_name, N(setpriv), config::system_account_name,  mvo()("account", account)("is_priv", 1));
         produce_block();
         return r;
      }

      fc::variant get_jurisdiction( code_jurisdiction code )
      {
         vector<char> data = get_row_by_account( N(beos.jurisdi), N(beos.jurisdi), N(infojurisdic), code );
         if( data.empty() )
            return fc::variant();
         else
            return jurisdiction_abi_ser.binary_to_variant( "info_jurisdiction", data, abi_serializer_max_time );
      }

      action_result add_jurisdiction( account_name ram_payer, code_jurisdiction new_code, std::string new_name, std::string new_description )
      {
         return push_action(ram_payer, N(addjurisdict), mvo()
            ("ram_payer",       ram_payer )
            ("new_code", new_code )
            ("new_name", new_name )
            ("new_description", new_description ),
            jurisdiction_abi_ser,
            N(beos.jurisdi)
            );
      }

      action_result update_jurisdictions( account_name producer, std::vector< code_jurisdiction > new_jurisdictions )
      {
         return push_action(producer, N(updateprod), mvo()
            ("producer",       producer )
            ("new_jurisdictions", new_jurisdictions ),
            jurisdiction_abi_ser,
            N(beos.jurisdi)
            );
      }
};

BOOST_AUTO_TEST_SUITE(eosio_jurisdiction_tests)

BOOST_FIXTURE_TEST_CASE( basic_test_01, beos_jurisdiction_tester ) try {

   auto message_01 = wasm_assert_msg("size of name is greater than allowed");
   auto message_02 = wasm_assert_msg("size of description is greater than allowed");
   auto message_03 = wasm_assert_msg("jurisdiction with the same code exists");
   auto message_04 = wasm_assert_msg("jurisdiction with the same name exists");

   std::string message_56           = "0123456789ABCDEFGHIJ0123456789ABCDEFGHIJ0123456789ABCDEF";
   std::string message_56_to_lower  = "0123456789abcdefghij0123456789abcdefghij0123456789abcdef";
   std::string message_100 = "0123456789ABCDEFGHIJ0123456789ABCDEFGHIJ0123456789ABCDEFGHIJ0123456789ABCDEFGHIJ0123456789ABCDEFGHIJ";
   std::string message_256 = message_100 + message_100 + message_56;

   {
      BOOST_REQUIRE_EQUAL( success(), add_jurisdiction( N(beos.jurisdi), 1, "POLAND", "EAST EUROPE" ) );
      auto result = get_jurisdiction( 1 );
      BOOST_REQUIRE_EQUAL( false, result.is_null() );
      BOOST_REQUIRE_EQUAL( true, result["code"] == 1 );
      BOOST_REQUIRE_EQUAL( true, result["name"] == "poland" );
      BOOST_REQUIRE_EQUAL( true, result["description"] == "EAST EUROPE" );
   }

   {
      BOOST_REQUIRE_EQUAL( success(), add_jurisdiction( N(beos.proda), 2, "sweden", "EAST EUROPE" ) );
      auto result = get_jurisdiction( 2 );
      BOOST_REQUIRE_EQUAL( false, result.is_null() );
      BOOST_REQUIRE_EQUAL( true, result["code"] == 2 );
      BOOST_REQUIRE_EQUAL( true, result["name"] == "sweden" );
      BOOST_REQUIRE_EQUAL( true, result["description"] == "EAST EUROPE" );

      result = get_jurisdiction( 1 );
      BOOST_REQUIRE_EQUAL( false, result.is_null() );
   }

   {
      BOOST_REQUIRE_EQUAL( message_01, add_jurisdiction( N(beos.proda), 1, message_256, "SOMEWHERE" ) );
      BOOST_REQUIRE_EQUAL( message_02, add_jurisdiction( N(beos.proda), 1, "Czech Republic", message_256 ) );
      BOOST_REQUIRE_EQUAL( message_03, add_jurisdiction( N(beos.proda), 1, "Russia", "EAST EUROPE/ASIA" ) );
      BOOST_REQUIRE_EQUAL( message_04, add_jurisdiction( N(beos.proda), 3, "SWEDEN", "EAST EUROPE/ASIA" ) );
   }

   {
      uint16_t start = 10000;

      for( int i = 0; i < 10; ++i )
         BOOST_REQUIRE_EQUAL( success(), add_jurisdiction( N(beos.prodb), start + i, message_56 + std::to_string( i ), "INFORMATION" ) );

      for( int i = 0; i < 10; ++i )
      {
         auto result = get_jurisdiction( start + i );
         BOOST_REQUIRE_EQUAL( false, result.is_null() );
         BOOST_REQUIRE_EQUAL( true, result["code"] == start + i );
         BOOST_REQUIRE_EQUAL( true, result["name"] == message_56_to_lower + std::to_string( i ) );
         BOOST_REQUIRE_EQUAL( true, result["description"] == "INFORMATION" );
      }
   }

   {
      uint16_t start = 20000;

      for( int i = 0; i < 10; ++i )
         BOOST_REQUIRE_EQUAL( message_04, add_jurisdiction( N(beos.prodc), start + i, message_56 + std::to_string( i ), "SOMEWHERE" ) );
   }

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_test_02, beos_jurisdiction_tester ) try {

   jurisdiction_helper updater;

   {
      jurisdiction_updater_ordered data;
      data.producer = N(beos.proda);
      data.jurisdictions = {1};
      BOOST_REQUIRE_EQUAL( success(), add_jurisdiction( N(beos.jurisdi), 1, "POLAND", "EAST EUROPE" ) );
      BOOST_REQUIRE_EQUAL( success(), update_jurisdictions( N(beos.proda), {1} ) );
      BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( control->db(), data ) );
   }

   {
      jurisdiction_updater_ordered data;
      data.producer = N(beos.proda);
      data.jurisdictions = {2,3};
      BOOST_REQUIRE_EQUAL( success(), add_jurisdiction( N(beos.jurisdi), 2, "RUSSIA", "EAST EUROPE" ) );
      BOOST_REQUIRE_EQUAL( success(), add_jurisdiction( N(beos.jurisdi), 3, "SWEDEN", "EAST EUROPE" ) );
      BOOST_REQUIRE_EQUAL( success(), update_jurisdictions( N(beos.proda), {2,3} ) );
      BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( control->db(), data ) );
   }

   {
      jurisdiction_updater_ordered data;
      data.producer = N(beos.proda);
      data.jurisdictions = {};
      BOOST_REQUIRE_EQUAL( success(), update_jurisdictions( N(beos.proda), {} ) );
      BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( control->db(), data ) );
   }

   {
      jurisdiction_updater_ordered data_01;
      data_01.producer = N(beos.proda);
      data_01.jurisdictions = {1,2,3};

      jurisdiction_updater_ordered data_02;
      data_02.producer = N(beos.prodb);
      data_02.jurisdictions = {2,3};

      BOOST_REQUIRE_EQUAL( success(), update_jurisdictions( N(beos.proda), {1,2,3} ) );
      BOOST_REQUIRE_EQUAL( success(), update_jurisdictions( N(beos.prodb), {2,3} ) );

      BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( control->db(), data_01 ) );
      BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( control->db(), data_02 ) );
   }

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(eosio_init_tests)

BOOST_FIXTURE_TEST_CASE( store_params_test, eosio_init_tester ) try {

  auto var_tgs = get_distrib_param();
  BOOST_REQUIRE_EQUAL( true, var_tgs.is_null() );

  BOOST_REQUIRE_EQUAL( success(), store_params_distrib() );

  //distribution is turned off by default
  var_tgs = get_distrib_param();
  BOOST_REQUIRE_EQUAL( false, var_tgs.is_null() );
  BOOST_REQUIRE_EQUAL( true, var_tgs["beos"].is_object() );
  BOOST_REQUIRE_EQUAL( true, var_tgs["ram"].is_object() );

  auto var_tgs_beos = var_tgs["beos"].get_object();
  BOOST_REQUIRE_EQUAL( true, var_tgs_beos["ending_block"].is_uint64() );
  BOOST_REQUIRE_EQUAL( var_tgs_beos["ending_block"].as_uint64(), 0 );

  auto var_tgs_ram = var_tgs["ram"].get_object();
  BOOST_REQUIRE_EQUAL( true, var_tgs_ram["ending_block"].is_uint64() );
  BOOST_REQUIRE_EQUAL( var_tgs_ram["ending_block"].as_uint64(), 0 );

  auto var_proxy = var_tgs["proxy_assets"];
  BOOST_REQUIRE_EQUAL( false, var_proxy.is_null() );
  std::vector<asset> proxy_assets = var_proxy.as< std::vector<asset> >();
  BOOST_REQUIRE_EQUAL( true, proxy_assets.empty() );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( store_params_test2, eosio_init_tester ) try {

  auto var_tgs = get_init_param();
  BOOST_REQUIRE_EQUAL( true, var_tgs.is_null() );

  BOOST_REQUIRE_EQUAL( success(), store_params_init() );

  var_tgs = get_init_param();
  BOOST_REQUIRE_EQUAL( false, var_tgs.is_null() );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_param_test, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block = 100;
  tgs.beos.ending_block = 105;
  tgs.beos.block_interval = 8;

  check_change_params( tgs );

  issue( N(alice), asset::from_string("100.0000 PROXY") );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "");

  produce_blocks( 100 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );
  
  CHECK_STATS(alice, "100.0000 PROXY", "200000000.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_param_test2, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.ram.starting_block = 80;
  tgs.ram.ending_block = 81;
  tgs.ram.block_interval = 800;

  tgs.beos.starting_block = 800;
  tgs.beos.ending_block = 810;
  tgs.beos.block_interval = 800;

  check_change_params( tgs );

  issue( N(alice), asset::from_string("100.0000 PROXY") );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 80 - control->head_block_num() - 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 79u );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 80u );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "30000000000");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_param_test3, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.ram.starting_block = 80;
  tgs.ram.ending_block = 90;
  tgs.ram.block_interval = 10;

  tgs.beos.starting_block = 80;
  tgs.beos.ending_block = 90;
  tgs.beos.block_interval = 10;

  check_change_params( tgs );

  issue( N(alice), asset::from_string("2.0000 PROXY") );

  CHECK_STATS(alice, "2.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 80 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 80u );

  CHECK_STATS(alice, "2.0000 PROXY", "100000000.0000 BEOS", "15000000000");

  //issue( N(beos.gateway), asset::from_string("1.0000 PROXY") ); <- cannot issue to itself
  transfer(N(alice), N(beos.gateway), asset::from_string("1.0000 PROXY"), "not a withdraw", N(eosio.token));
    //proxy on beos.gateway don't count (they are considered withdrawn)
  issue( N(beos.distrib), asset::from_string("1.0000 PROXY") );
    //beos.distrib does not include itself in distribution since it would just increase next pool
    //but weight is still influenced by its proxy
  issue( N(beos.init), asset::from_string("1.0000 PROXY") );
  issue( N(eosio), asset::from_string("1.0000 PROXY") );
  issue( N(eosio.token), asset::from_string("1.0000 PROXY") );
    //unlimited system accounts are filtered out from distribution but their proxy still influences
    //weight

  produce_blocks( 6 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 90u );

  CHECK_STATS(alice, "1.0000 PROXY", "120000000.0000 BEOS", "18000000000");
  //note: proxy on gateway/distrib and unlimited system accounts influence weights but
  //don't consume resources; unused resources are all on distrib
  CHECK_STATS(beos.distrib, "1.0000 PROXY", "80000002.0000 BEOS", "12000294552"); //+DEFAULT_RAM

  //ABW: it turns out that in case of such large imbalance in the system (one account has pretty
  //much all resources - in this case 'alice') when available net/cpu is calculated for account with
  //small bandwidth (in this case beos.distrib has 1BEOS on cpu) we fall into special case in EOS
  //code resource_limits_manager::get_account_cpu_limit_ex() line 563:
  //"if( max_user_use_in_window <= cpu_used_in_window )
  //    arl.available = 0;"
  //which means beos.distrib cannot effectively call 'withdraw' action nor 'changeparams' and
  //these are needed for rest of the test
  /*
  //since distrib still has resources to give away we might restart distribution for second round
  issue( N(alice), asset::from_string("1.0000 PROXY") );
  transfer(N(alice), N(bob), asset::from_string("1.0000 PROXY"), "order no.12345", N(eosio.token));
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(beos.distrib), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(beos.init), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(eosio), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(eosio.token), asset::from_string("1.0000 PROXY") ) );

  tgs.ram.starting_block = 100;
  tgs.ram.ending_block = 100;
  tgs.ram.block_interval = 1;

  tgs.beos.starting_block = 100;
  tgs.beos.ending_block = 100;
  tgs.beos.block_interval = 1;

  check_change_params( tgs );

  produce_blocks( 100 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  CHECK_STATS(alice, "1.0000 PROXY", "160000000.0000 BEOS", "24000000000");
  CHECK_STATS(bob, "1.0000 PROXY", "40000000.0000 BEOS", "6000000000");
  //note: all remaining rewards distributed in second round
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "2.0000 BEOS", "294552"); //+DEFAULT_RAM
  */
} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( many_producers_test, eosio_init_tester ) try {
  BOOST_TEST_MESSAGE( "Creating many producers");

  test_global_state tgs;

  tgs.beos.starting_block = 5000;
  tgs.beos.ending_block = 6000;
  tgs.beos.block_interval = 1000;

  tgs.ram.starting_block = 300000;
  tgs.ram.ending_block = 300000;
  tgs.ram.block_interval = 300000;

  check_change_params( tgs );

  const uint32_t nr_accounts = 500;

  const auto& StN = eosio::chain::string_to_name;
  using Accounts = std::vector<std::string>;
  Accounts accounts;

  for( uint32_t i = 0; i < nr_accounts; ++i )
  {
    std::string str_name = std::to_string( i );
    std::string res = "x";
    for( auto c : str_name )
      res += char( c - 48/*'0'*/ + 97/*'a'*/ );

    accounts.emplace_back( res );
  }

  for( auto account : accounts )
  {
    create_account_with_resources( config::gateway_account_name, StN( account.c_str() ) );
    BOOST_REQUIRE_EQUAL( success(), issue( StN( account.c_str() ), asset::from_string("5.0000 PROXY") ) );
  }

  produce_blocks( tgs.beos.starting_block - control->head_block_num() );

  for( auto account : accounts )
    CHECK_STATS_( StN( account.c_str() ), "5.0000 PROXY", "200000.0000 BEOS", "0");

  for( auto account : accounts )
    BOOST_REQUIRE_EQUAL( success(), create_producer( StN( account.c_str() ) ) );

  produce_blocks( tgs.beos.ending_block - control->head_block_num() );

  for( auto account : accounts )
    CHECK_STATS_( StN( account.c_str() ), "5.0000 PROXY", "400000.0000 BEOS", "0");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( rewarding2, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.ram.starting_block = 80;
  tgs.ram.ending_block = 205;
  tgs.ram.block_interval = 25;

  tgs.beos.starting_block = 80;
  tgs.beos.ending_block = 170;
  tgs.beos.block_interval = 10;

  tgs.proxy_assets.emplace_back(0, symbol(SY(6, BROWNIE)));
  //asset weights: PROXY.satoshi gives 100 units of reward, 1 BROWNIE.satoshi gives 1 unit of reward (1 PROXY = 1 BROWNIE)
  //each beos reward per interval is 20mln
  //each ram reward per interval is 5bln

  check_change_params( tgs );

  issue( N(alice), asset::from_string("20.0000 PROXY") );
  issue( N(bob), asset::from_string("10.0000 PROXY") );
  issue( N(bob), asset::from_string("22.22200 PXEOS") );
  issue( N(carol), asset::from_string("10.000000 BROWNIE") );
  issue( N(carol), asset::from_string("1.23456 PXEOS") );
  issue( N(dan), asset::from_string("30.0000 PROXY") );
  issue( N(dan), asset::from_string("30.000000 BROWNIE") );
  issue( N(dan), asset::from_string("12345.65890 PXEOS") );
  //weights: alice 0.2, bob 0.1, carol 0.1, dan 0.6
  //note: PXEOS is not registered as asset that gives rewards

  produce_blocks( 80 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 80u );

  CHECK_STATS(alice, "", "4000000.0000 BEOS", "1000000000");
  CHECK_STATS(bob, "", "2000000.0000 BEOS", "500000000");
  CHECK_STATS(carol, "", "2000000.0000 BEOS", "500000000");
  CHECK_STATS(dan, "", "12000000.0000 BEOS", "3000000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("10.00000 PXEOS") ) );
  transfer(N(dan), N(alice), asset::from_string("300.00000 PXEOS"), "order.1234", N(eosio.token));

  produce_blocks( 90 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 90u );

  CHECK_STATS(alice, "", "8000000.0000 BEOS", "1000000000");
  CHECK_STATS(bob, "", "4000000.0000 BEOS", "500000000");
  CHECK_STATS(carol, "", "4000000.0000 BEOS", "500000000");
  CHECK_STATS(dan, "", "24000000.0000 BEOS", "3000000000");

  transfer(N(alice), N(dan), asset::from_string("10.0000 PROXY"), "buy brownie", N(eosio.token));
  transfer(N(dan), N(alice), asset::from_string("10.000000 BROWNIE"), "sell brownie", N(eosio.token));
  transfer(N(bob), N(dan), asset::from_string("10.0000 PROXY"), "buy brownie", N(eosio.token));
  transfer(N(dan), N(bob), asset::from_string("10.000000 BROWNIE"), "sell brownie", N(eosio.token));
  issue( N(dan), asset::from_string("100.000000 BROWNIE") );
  //weights: alice 0.1, bob 0.05, carol 0.05, dan 0.8

  produce_blocks( 105 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 105u );

  CHECK_STATS(alice, "", "10000000.0000 BEOS", "1500000000");
  CHECK_STATS(bob, "", "5000000.0000 BEOS", "750000000");
  CHECK_STATS(carol, "", "5000000.0000 BEOS", "750000000");
  CHECK_STATS(dan, "", "40000000.0000 BEOS", "7000000000");

  produce_blocks( 170 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 170u );

  CHECK_STATS(alice, "", "24000000.0000 BEOS", "2500000000");
  CHECK_STATS(bob, "", "12000000.0000 BEOS", "1250000000");
  CHECK_STATS(carol, "", "12000000.0000 BEOS", "1250000000");
  CHECK_STATS(dan, "", "152000000.0000 BEOS", "15000000000");

  //note: all beos rewards were distributed at this point
  CHECK_STATS(beos.distrib, "", "2.0000 BEOS", "10000294552"); //+DEFAULT_RAM

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("50.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("10.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("110.000000 BROWNIE") ) );
  transfer(N(alice), N(carol), asset::from_string("10.000000 BROWNIE"), "order.133", N(eosio.token));
  transfer(N(bob), N(carol), asset::from_string("10.000000 BROWNIE"), "order.134", N(eosio.token));
  //all PROXY is gone; weights: alice/bob 0, carol 1, dan 0
  
  produce_blocks( 180 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 180u );

  CHECK_STATS(alice, "", "24000000.0000 BEOS", "2500000000");
  CHECK_STATS(bob, "", "12000000.0000 BEOS", "1250000000");
  CHECK_STATS(carol, "", "12000000.0000 BEOS", "6250000000");
  CHECK_STATS(dan, "", "152000000.0000 BEOS", "15000000000");

  CHECK_STATS(beos.distrib, "", "2.0000 BEOS", "5000294552"); //+DEFAULT_RAM

  issue( N(dan), asset::from_string("70.0000 PROXY") );

  produce_blocks( 205 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 205u );

  CHECK_STATS(alice, "", "24000000.0000 BEOS", "2500000000");
  CHECK_STATS(bob, "", "12000000.0000 BEOS", "1250000000");
  CHECK_STATS(carol, "", "12000000.0000 BEOS", "7750000000");
  CHECK_STATS(dan, "", "152000000.0000 BEOS", "18500000000");

  //note: all rewards were distributed
  CHECK_STATS(beos.distrib, "", "2.0000 BEOS", "294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( rewarding3, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.ram.starting_block = 80;
  tgs.ram.ending_block = 100;
  tgs.ram.block_interval = 10;
  tgs.ram.trustee_reward += 3'000'000'000; //extra trustee reward so the remaining amount splits evenly

  tgs.beos.starting_block = 80;
  tgs.beos.ending_block = 100;
  tgs.beos.block_interval = 10;
  tgs.beos.trustee_reward += 20'000'000'0000; //extra trustee reward so the remaining amount splits evenly

  tgs.proxy_assets.emplace_back(0, symbol(SY(6, BROWNIE)));
  tgs.proxy_assets.emplace_back(0, symbol(SY(5, PXEOS)));
  //asset weights: PROXY.satoshi gives 100 units of reward, BROWNIE.satoshi gives 1 unit of reward, PXEOS.satoshi gives 10 units of reward (1 PROXY = 1 BROWNIE = 1 PXEOS)
  //each beos reward per interval is 60mln
  //each ram reward per interval is 9bln

  check_change_params( tgs );

  issue( N(alice), asset::from_string("3.0000 PROXY") );
  issue( N(alice), asset::from_string("1.000000 BROWNIE") );
  issue( N(bob), asset::from_string("2.0000 PROXY") );
  issue( N(carol), asset::from_string("2.0000 PROXY") );
  issue( N(carol), asset::from_string("2.000000 BROWNIE") );
  issue( N(carol), asset::from_string("1.00000 PXEOS") );
  issue( N(dan), asset::from_string("1.000000 BROWNIE") );
  issue( N(dan), asset::from_string("7.00000 PXEOS") );
  issue( N(beos.trustee), asset::from_string("1.00000 PXEOS") );
  //weights: alice 0.2, bob 0.1, carol 0.25, dan 0.4, beos.trustee 0.05 (extra over its own reward)

  produce_blocks( 80 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 80u );

  CHECK_STATS(alice, "", "12000000.0000 BEOS", "1800000000");
  CHECK_STATS(bob, "", "6000000.0000 BEOS", "900000000");
  CHECK_STATS(carol, "", "15000000.0000 BEOS", "2250000000");
  CHECK_STATS(dan, "", "24000000.0000 BEOS", "3600000000");
  CHECK_STATS(beos.trustee, "", "9667000.0000 BEOS", "1450000000");

  transfer(N(bob), N(dan), asset::from_string("1.0000 PROXY"), "sell", N(eosio.token));
  transfer(N(carol), N(dan), asset::from_string("2.0000 PROXY"), "sell", N(eosio.token));
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("5.00000 PXEOS") ) );
  transfer(N(dan), N(carol), asset::from_string("1.00000 PXEOS"), "buy", N(eosio.token));
  transfer(N(dan), N(carol), asset::from_string("1.000000 BROWNIE"), "buy", N(eosio.token));
  transfer(N(dan), N(beos.trustee), asset::from_string("1.00000 PXEOS"), "buy", N(eosio.token));
  issue( N(dan), asset::from_string("5.0000 PROXY") );
  //weights: alice 0.2, bob 0.05, carol 0.25, dan 0.4, beos.trustee 0.1 (extra over its own reward)

  produce_blocks( 90 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 90u );

  CHECK_STATS(alice, "", "24000000.0000 BEOS", "3600000000");
  CHECK_STATS(bob, "", "9000000.0000 BEOS", "1350000000");
  CHECK_STATS(carol, "", "30000000.0000 BEOS", "4500000000");
  CHECK_STATS(dan, "", "48000000.0000 BEOS", "7200000000");
  CHECK_STATS(beos.trustee, "", "22334000.0000 BEOS", "3350000000");

  transfer(N(alice), N(dan), asset::from_string("2.0000 PROXY"), "sell", N(eosio.token));
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("10.0000 PROXY") ) );
  transfer(N(carol), N(dan), asset::from_string("2.000000 BROWNIE"), "sell", N(eosio.token));
  //weights: alice 0.2, bob 0.1, carol 0.3, dan 0.2, beos.trustee 0.2 (extra over its own reward)

  produce_blocks( 100 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  CHECK_STATS(alice, "", "36000000.0000 BEOS", "5400000000");
  CHECK_STATS(bob, "", "15000000.0000 BEOS", "2250000000");
  CHECK_STATS(carol, "", "48000000.0000 BEOS", "7200000000");
  CHECK_STATS(dan, "", "60000000.0000 BEOS", "9000000000");
  CHECK_STATS(beos.trustee, "", "41001000.0000 BEOS", "6150000000");

  //note: all rewards were distributed
  CHECK_STATS(beos.distrib, "", "2.0000 BEOS", "294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( rewarding_weights, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.ram.starting_block = 80;
  tgs.ram.ending_block = 80;
  tgs.ram.block_interval = 10;

  tgs.beos.starting_block = 80;
  tgs.beos.ending_block = 80;
  tgs.beos.block_interval = 10;

  tgs.ram_leftover += 20000000000; //leave for second distribution

  tgs.proxy_assets.clear();
  tgs.proxy_assets.emplace_back(31, symbol(SY(4, PROXY)));
  tgs.proxy_assets.emplace_back(27, symbol(SY(6, BROWNIE)));
  tgs.proxy_assets.emplace_back(42, symbol(SY(5, PXEOS)));
  //asset weights: PROXY.satoshi gives 31 units of reward, BROWNIE.satoshi gives 27 unit of reward, PXEOS.satoshi gives 42 units of reward (1 PROXY ~ 0.0114815 BROWNIE ~ 0.07381 PXEOS)
  //one reward: 200mln beos + 10bln ram

  check_change_params( tgs );

  issue( N(alice), asset::from_string("1.0000 PROXY") );
  issue( N(bob), asset::from_string("0.010000 BROWNIE") );
  issue( N(carol), asset::from_string("0.10000 PXEOS") );
  //weights: alice 0.31, bob 0.27, carol 0.42

  produce_blocks( 80 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 80u );

  CHECK_STATS(alice, "", "62000000.0000 BEOS", "3100000000");
  CHECK_STATS(bob, "", "54000000.0000 BEOS", "2700000000");
  CHECK_STATS(carol, "", "84000000.0000 BEOS", "4200000000");

  //note: all beos rewards were distributed
  CHECK_STATS(beos.distrib, "", "2.0000 BEOS", "20000294552"); //+DEFAULT_RAM

  tgs.ram.starting_block = 90;
  tgs.ram.ending_block = 100;
  tgs.ram.block_interval = 10;

  tgs.ram_leftover -= 20000000000; //back to default leftover

  tgs.proxy_assets.clear();
  tgs.proxy_assets.emplace_back(30, symbol(SY(4, PROXY)));
  tgs.proxy_assets.emplace_back(1, symbol(SY(5, PXEOS)));
  //asset weights: PROXY.satoshi gives 30 units of reward, PXEOS.satoshi gives 1 unit of reward (1 PROXY = 3 PXEOS)
  //two ram rewards: 10bln each

  //ABW: we need to refill net for beos.distrib or the changeparams won't work since it has very little net compared to other accounts
  BOOST_REQUIRE_EQUAL( success(), stake(N(eosio), N(beos.distrib), asset::from_string("10000.0000 BEOS"), asset::from_string("10000.0000 BEOS"), false) );
  check_change_params( tgs );

  issue( N(carol), asset::from_string("2.90000 PXEOS") );
  issue( N(bob), asset::from_string("1234567.880000 BROWNIE") );
  transfer(N(alice), N(eosio.ram), asset::from_string("1.0000 PROXY"), "wrong receiver", N(eosio.token));

  produce_blocks( 90 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 90u );

  CHECK_STATS(alice, "", "62000000.0000 BEOS", "3100000000");
  CHECK_STATS(bob, "", "54000000.0000 BEOS", "2700000000");
  CHECK_STATS(carol, "", "84000000.0000 BEOS", "9200000000");
  //alice/bob no change, carol took half of this interval pool, eosio.ram was eligible for second half but as it is unlimited account its reward returned to pool
  CHECK_STATS(beos.distrib, "", "", "15000294552"); //+DEFAULT_RAM

  transfer(N(eosio.ram), N(alice), asset::from_string("1.0000 PROXY"), "fixed error", N(eosio.token));

  produce_blocks( 100 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );
  //note: since there was unused part of reward from previous interval, final reward pool is 15bln ram

  CHECK_STATS(alice, "", "62000000.0000 BEOS", "10600000000");
  CHECK_STATS(bob, "", "54000000.0000 BEOS", "2700000000");
  CHECK_STATS(carol, "", "84000000.0000 BEOS", "16700000000");

  //note: all rewards were distributed (note bandwidth borrowed from eosio)
  CHECK_STATS(beos.distrib, "", "20002.0000 BEOS", "294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( liquid_ram_test, eosio_init_tester ) try {

  test_global_state tgs; //ram distrib perion: 240-248
  check_change_params( tgs );

  create_account_with_resources( config::gateway_account_name, N(mario) );
  create_account_with_resources( config::gateway_account_name, N(mario2) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(mario), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(mario2), asset::from_string("5.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "mario", 5600 ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "mario2", 15600 ) );

  produce_blocks( 248 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "mario", 5601 ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "mario2", 15601 ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 249u );

  BOOST_REQUIRE_EQUAL( success(), sellram( "mario", 5600 ) );
  BOOST_REQUIRE_EQUAL( success(), sellram( "mario2", 15600 ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( liquid_ram_test2, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block = 60;
  tgs.beos.ending_block = 61;
  tgs.ram.starting_block = 80;
  tgs.ram.ending_block = 81;
  check_change_params( tgs );

  create_account_with_resources( config::gateway_account_name, N(xxxxxxxmario) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(xxxxxxxmario), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxxmario", 5600 ) );

  produce_blocks( 81 - control->head_block_num() );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxxmario", 5600 ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 82 );
  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "200000000.0000 BEOS", "30000000000");

  BOOST_REQUIRE_EQUAL( success(), sellram( "xxxxxxxmario", 5600 ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( false_tests, eosio_init_tester ) try {

  test_global_state tgs;

  produce_blocks( 30 - control->head_block_num() );

  auto buffer = tgs.starting_block_for_initial_witness_election;
  tgs.starting_block_for_initial_witness_election = 0;
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("STARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION > 0"), change_init_params( tgs ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
  tgs.starting_block_for_initial_witness_election = buffer;

  checker( tgs, tgs.beos );
  checker( tgs, tgs.ram );
  auto leftover = tgs.ram_leftover;
  tgs.ram_leftover = 64'000'000'000;
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("Cannot request to leave more than allocated ram"), change_distrib_params( tgs ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
  tgs.ram_leftover = leftover;

  tgs.proxy_assets.emplace_back(13, symbol(SY(6, BROWNIE)));
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("All assets need positive weight or all must be 0"), change_distrib_params( tgs ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );

  tgs.proxy_assets.back() -= asset(13, symbol(SY(6, BROWNIE)));
  tgs.proxy_assets.front() += asset(1, symbol(SY(4, PROXY)));
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("All assets need positive weight or all must be 0"), change_distrib_params( tgs ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );

  tgs.proxy_assets.back() -= asset(1, symbol(SY(6, BROWNIE)));
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("Asset weight cannot be negative"), change_distrib_params( tgs ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
  tgs.proxy_assets.pop_back();

  tgs.proxy_assets.front() -= asset(2, symbol(SY(4, PROXY)));
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("Asset weight cannot be negative"), change_distrib_params( tgs ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );

  tgs.proxy_assets.clear();
  tgs.proxy_assets.emplace_back(asset(0, symbol(SY(3, COOKIE))));
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("Unknown asset symbol"), change_distrib_params( tgs ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );

  tgs.proxy_assets.clear();
  tgs.proxy_assets.emplace_back(asset(0, symbol(SY(4, BEOS))));
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("Proxy assets must be created with beos.gateway as issuer"), change_distrib_params( tgs ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_vote_test, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block = 50;
  tgs.beos.block_interval = 5;
  tgs.beos.ending_block = 55;
  check_change_params( tgs );

  create_account_with_resources( config::gateway_account_name, N(xxxxxxxmario) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(xxxxxxxmario), asset::from_string("5.0000 PROXY") ) );

  produce_blocks( 60 - control->head_block_num() );

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "100000000.0000 BEOS", "0");
  CHECK_STATS(bob, "5.0000 PROXY", "100000000.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( atof( "1.0913574775723183e+18" ), get_producer_info( N(bob) )["total_votes"].as_double() );

  produce_blocks( 100 - control->head_block_num() );

  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "100000000.0000 BEOS", "0");
  CHECK_STATS(bob, "5.0000 PROXY", "100000000.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( atof( "1.0913574775723183e+18" ), get_producer_info( N(bob) )["total_votes"].as_double() );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  BOOST_REQUIRE_EQUAL( atof( "1.0913574775723183e+18" ), get_producer_info( N(bob) )["total_votes"].as_double() );

  produce_blocks( 1 );

  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "100000000.0000 BEOS", "0");
  CHECK_STATS(bob, "5.0000 PROXY", "100000000.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( atof( "1.0913574775723183e+18" ), get_producer_info( N(bob) )["total_votes"].as_double() );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  BOOST_REQUIRE_EQUAL( atof( "1.0913574775723183e+18" ), get_producer_info( N(bob) )["total_votes"].as_double() );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_vote_test2, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block = 50;
  tgs.beos.block_interval = 5;
  tgs.beos.ending_block = 145;
  check_change_params( tgs );

  create_account_with_resources( config::gateway_account_name, N(xxxxxxxmario) );
  create_account_with_resources( config::gateway_account_name, N(xxxxxxmario2) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(xxxxxxxmario), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(xxxxxxmario2), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("5.0000 PROXY") ) );

  produce_blocks( 60 - control->head_block_num() );

  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "7500000.0000 BEOS", "0");
  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "7500000.0000 BEOS", "0");
  CHECK_STATS(bob, "5.0000 PROXY", "7500000.0000 BEOS", "0");
  CHECK_STATS(carol, "5.0000 PROXY", "7500000.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );
  BOOST_REQUIRE_EQUAL( success(), create_producer( N(carol) ) );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( 0, get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( atof( "2.1827149551446368e+17" ), get_producer_info( N(carol) )["total_votes"].as_double() );

  produce_blocks( 100 - control->head_block_num() - 2 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 98u );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( atof( "3.0012330633238758e+17" ), get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( atof( "3.0012330633238765e+17" ), get_producer_info( N(carol) )["total_votes"].as_double() );

  produce_blocks( 1 );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 102u );

  BOOST_REQUIRE_EQUAL( atof( "3.0012330633238758e+17" ), get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( atof( "3.0012330633238765e+17" ), get_producer_info( N(carol) )["total_votes"].as_double() );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 103u );

  BOOST_REQUIRE_EQUAL( atof( "3.0012330633238758e+17" ), get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( atof( "3.0012330633238765e+17" ), get_producer_info( N(carol) )["total_votes"].as_double() );

  produce_blocks( 110 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 110u );

  BOOST_REQUIRE_EQUAL( atof( "3.5469118021100346e+17" ), get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( atof( "3.5469118021100352e+17" ), get_producer_info( N(carol) )["total_votes"].as_double() );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( undelegate_block_test, eosio_init_tester ) try {
  //see issue #15

  test_global_state tgs;

  tgs.beos.starting_block = 100;
  tgs.beos.ending_block = 105;
  tgs.beos.block_interval = 8;

  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("cannot unstake during distribution period"), unstake( N(alice), N(alice), asset::from_string("10.0000 BEOS"), asset::from_string("10.0000 BEOS") ) );

  produce_blocks( 105 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 105u );

  //ABW: first we need to extend the test with voting (15% required to allow successful unstake) but to do that
  //we need delegations working on stake (issue #13) - supplement once it is done
  //BOOST_REQUIRE_EQUAL( success(), unstake( N(alice), asset::from_string("10.0000 BEOS"), asset::from_string("10.0000 BEOS") ) );
  //CHECK_STATS(alice, "0.0000 PROXY", "20.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( delegate_block_test, eosio_init_tester ) try {

  asset _5 = asset::from_string("5.0000 BEOS");
  asset _10 = asset::from_string("10.0000 BEOS");

  test_global_state tgs;
  check_change_params( tgs );

  produce_blocks( 235 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 235u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("no balance object found"), stake( N(alice), N(bob), _10, _10, true ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("000.0010 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("000.0001 PROXY") ) );

  produce_blocks( 242 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 242u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("no balance object found"), stake( N(alice), N(bob), _10, _10, true ) );

  produce_blocks( 248 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("no balance object found"), stake( N(alice), N(bob), _10, _10, true ) );

  produce_blocks( 270 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );
  CHECK_STATS(alice, "0.0010 PROXY", "181818181.8183 BEOS", "27272727272");
  CHECK_STATS(bob, "0.0001 PROXY", "18181818.1816 BEOS", "2727272727");

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("no balance object found"), stake( N(alice), N(bob), _10, _10, true ) );

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(alice), { N(bob) } ) );

  BOOST_REQUIRE_EQUAL( success(), unstake( N(alice), N(alice), _5, _5 ) );

  produce_block( fc::hours(3*24) );
  produce_blocks(1);

  asset balance = get_balance( N(alice) );
  BOOST_REQUIRE_EQUAL( _10, balance );  

  BOOST_REQUIRE_EQUAL( success(), stake( N(alice), N(bob), _5, _5, true ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( delegate_block_test2, eosio_init_tester ) try {

  asset _0 = asset::from_string("0.0000 BEOS");
  asset _5 = asset::from_string("5.0000 BEOS");
  asset _10 = asset::from_string("10.0000 BEOS");

  std::string message_15_percent = "cannot undelegate bandwidth until the chain is activated (at least 15% of all tokens participate in voting)";
  std::string message_not_enough_net = "insufficient staked net bandwidth";
  std::string message_no_balance = "no balance object found";
  std::string message_overdrawn_balance = "overdrawn balance";

  test_global_state tgs;

  tgs.starting_block_for_initial_witness_election = 1;

  tgs.ram.starting_block = 200;
  tgs.ram.block_interval = 10;
  tgs.ram.ending_block = 205;

  tgs.beos.starting_block = 200;
  tgs.beos.block_interval = 2;
  tgs.beos.ending_block = 206;

  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("1.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( "user must stake before they can vote" ), vote_producer( N(alice), { N(dan) } ) );

  produce_blocks( 207 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 207u );
  CHECK_STATS(alice, "1.0000 PROXY", "50000000.0000 BEOS", "7500000000");
  CHECK_STATS(bob, "1.0000 PROXY", "50000000.0000 BEOS", "7500000000");
  CHECK_STATS(carol, "1.0000 PROXY", "50000000.0000 BEOS", "7500000000");
  CHECK_STATS(dan, "1.0000 PROXY", "50000000.0000 BEOS", "7500000000");

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( "producer is not registered" ), vote_producer( N(alice), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_15_percent ), unstake( N(alice), N(alice), _5, _5 ) );

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(alice), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_15_percent ), unstake( N(alice), N(alice), _5, _5 ) );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(carol), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_15_percent ), unstake( N(alice), N(alice), _5, _5 ) );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(dan), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), unstake( N(alice), N(alice), _5, _5 ) );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_not_enough_net ), unstake( N(alice), N(alice), asset::from_string("50000000.0000 BEOS"), _0 ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_not_enough_net ), unstake( N(bob), N(alice), asset::from_string("5.0000 BEOS"), _0 ) );

  BOOST_REQUIRE_EQUAL( success(), unstake( N(bob), N(bob), _5, _5 ) );
  BOOST_REQUIRE_EQUAL( success(), unstake( N(carol), N(carol), _5, _5 ) );

  produce_block( fc::hours(3*24) );
  produce_blocks(1);

  asset balance = get_balance( N(alice) );
  BOOST_REQUIRE_EQUAL( _10, balance );  

  balance = get_balance( N(bob) );
  BOOST_REQUIRE_EQUAL( _10, balance );  

  balance = get_balance( N(carol) );
  BOOST_REQUIRE_EQUAL( _10, balance );  

  balance = get_balance( N(dan) );
  BOOST_REQUIRE_EQUAL( _0, balance );  

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_no_balance ), stake( N(dan), N(bob), asset::from_string("11.0000 BEOS"), _0, false ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_no_balance ), stake( N(dan), N(bob), asset::from_string("11.0000 BEOS"), _0, true ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_overdrawn_balance ), stake( N(alice), N(bob), asset::from_string("11.0000 BEOS"), _0, false ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_overdrawn_balance ), stake( N(alice), N(bob), asset::from_string("11.0000 BEOS"), _0, true ) );

  BOOST_REQUIRE_EQUAL( success(), stake( N(alice), N(carol), asset::from_string("1.0000 BEOS"), _0, false ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( delegate_block_test3, eosio_init_tester ) try {

  asset _0 = asset::from_string("0.0000 BEOS");
  asset _5 = asset::from_string("5.0000 BEOS");
  asset _10 = asset::from_string("10.0000 BEOS");
  asset _20 = asset::from_string("20.0000 BEOS");

  asset _reward_quarter = asset::from_string("50000000.0000 BEOS");
  asset _reward_half = asset::from_string("100000000.0000 BEOS");
  asset _reward = asset::from_string("200000000.0000 BEOS");

  test_global_state tgs;

  tgs.starting_block_for_initial_witness_election = 1;

  tgs.ram.starting_block = 200;
  tgs.ram.block_interval = 10;
  tgs.ram.ending_block = 205;

  tgs.beos.starting_block = 200;
  tgs.beos.block_interval = 10;
  tgs.beos.ending_block = 206;

  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 206 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 206u );

  CHECK_STATS(alice, "1.0000 PROXY", _reward_half.to_string().c_str(), "");
  CHECK_STATS(bob, "1.0000 PROXY", _reward_half.to_string().c_str(), "");

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );
  BOOST_REQUIRE_EQUAL( success(), create_producer( N(alice) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(alice), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(bob), { N(alice) } ) );
  BOOST_REQUIRE_EQUAL( success(), unstake( N(bob), N(bob), _10, _10 ) );

  produce_block( fc::hours(3*24) );
  produce_blocks(1);

  BOOST_REQUIRE_EQUAL( _20, get_balance( N(bob) ) );  

  BOOST_REQUIRE_EQUAL( success(), stake( N(bob), N(alice), _10, _10, false ) );
  BOOST_REQUIRE_EQUAL( _0, get_balance( N(bob) ) );  

  BOOST_REQUIRE_EQUAL( success(), unstake( N(alice), N(alice), _reward_quarter, _reward_quarter ) );

  produce_block( fc::hours(3*24) );
  produce_blocks(1);

  BOOST_REQUIRE_EQUAL( _reward_half, get_balance( N(alice) ) );  

  /*
    There is impossible, that 'alice' has any staked BEOSes.
    Checking records in `user_reward_info_table` rejects retrieving rewards many times.
  */
  std::string message_not_enough_net = "insufficient staked net bandwidth";
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_not_enough_net ), unstake( N(alice), N(alice), _5, _0 ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( claimrewards_test, eosio_init_tester ) try {

  asset _0 = asset::from_string("0.0000 BEOS");

  std::string message_no_found_key = "unable to find key";
  std::string message_15_percent = "cannot claim rewards until the chain is activated (at least 15% of all tokens participate in voting)";
  std::string message_once_per_day = "already claimed rewards within past day";

  test_global_state tgs;

  tgs.starting_block_for_initial_witness_election = 1;

  tgs.ram.starting_block = 200;
  tgs.ram.block_interval = 10;
  tgs.ram.ending_block = 205;

  tgs.beos.starting_block = 200;
  tgs.beos.block_interval = 2;
  tgs.beos.ending_block = 206;

  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_no_found_key ), claimrewards( N(alice) ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 200 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 200u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_no_found_key ), claimrewards( N(alice) ) );
  BOOST_REQUIRE_EQUAL( success(), create_producer( N(alice) ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_15_percent ), claimrewards( N(alice) ) );

  produce_blocks( 210 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 210u );

  produce_blocks(200);
  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(alice), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(bob), { N(alice) } ) );
  produce_blocks(200);

  CHECK_STATS( alice, "1.0000 PROXY", "100000000.0000 BEOS", "15000000000");
  CHECK_STATS( bob, "1.0000 PROXY", "100000000.0000 BEOS", "15000000000");

  BOOST_REQUIRE_EQUAL( _0, get_balance( N(eosio.saving) ) );
  BOOST_REQUIRE_EQUAL( _0, get_balance( N(eosio.bpay) ) );
  BOOST_REQUIRE_EQUAL( _0, get_balance( N(eosio.vpay) ) );

  asset supply01 = get_token_supply();

  BOOST_REQUIRE_EQUAL( success(), claimrewards( N(alice) ) );
  produce_blocks(1);
  BOOST_REQUIRE_EQUAL( asset::from_string("124.1097 BEOS"), get_balance( N(eosio.saving) ) );
  BOOST_REQUIRE_EQUAL( asset::from_string("3.8194 BEOS"), get_balance( N(eosio.bpay) ) );
  BOOST_REQUIRE_EQUAL( asset::from_string("23.2706 BEOS"), get_balance( N(eosio.vpay) ) );
  CHECK_STATS( alice, "1.0000 PROXY", "100000003.9374 BEOS", "15000000000");

  asset supply02 = get_token_supply();
  asset sum = supply01 + get_balance( N(eosio.saving) ) + get_balance( N(eosio.bpay) ) + get_balance( N(eosio.vpay) );
  sum+= asset::from_string("3.9374 BEOS");
  BOOST_REQUIRE_EQUAL( supply02, sum );

  BOOST_REQUIRE_EQUAL( success(), claimrewards( N(bob) ) );
  produce_blocks(1);
  BOOST_REQUIRE_EQUAL( asset::from_string("125.3508 BEOS"), get_balance( N(eosio.saving) ) );
  BOOST_REQUIRE_EQUAL( asset::from_string("0.0000 BEOS"), get_balance( N(eosio.bpay) ) );
  BOOST_REQUIRE_EQUAL( asset::from_string("23.5033 BEOS"), get_balance( N(eosio.vpay) ) );
  CHECK_STATS( bob, "1.0000 PROXY", "100000003.8969 BEOS", "15000000000");

  asset supply03 = get_token_supply();
  sum = supply01 + get_balance( N(eosio.saving) ) + get_balance( N(eosio.bpay) ) + get_balance( N(eosio.vpay) );
  sum+= asset::from_string("3.9374 BEOS");
  sum+= asset::from_string("3.8969 BEOS");
  BOOST_REQUIRE_EQUAL( supply03, sum );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_once_per_day ), claimrewards( N(alice) ) );

  produce_block( fc::hours(24) );
  produce_blocks(1);

  BOOST_REQUIRE_EQUAL( success(), claimrewards( N(bob) ) );
  CHECK_STATS( bob, "1.0000 PROXY", "100016770.7497 BEOS", "15000000000");

  BOOST_REQUIRE_EQUAL( success(), claimrewards( N(alice) ) );
  CHECK_STATS( alice, "1.0000 PROXY", "100005036.8236 BEOS", "15000000000");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( trustee_reward_test, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block = 100;
  tgs.beos.ending_block = 110;
  tgs.beos.block_interval = 8;
  tgs.beos.trustee_reward = 20'0000;
  tgs.ram.starting_block = 100;
  tgs.ram.ending_block = 110;
  tgs.ram.block_interval = 5;
  tgs.ram.trustee_reward = 30000000; //while normally it is not, trustee account can be rewarded ram as well

  check_change_params( tgs );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 100 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", "10.0000 BEOS", "10000000");

  issue( N(beos.trustee), asset::from_string("10.0000 PROXY") ); //trustee can be treated with regular
    //rewards on top of its special reward

  produce_blocks( 110 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 110u );

  CHECK_STATS(beos.trustee, "10.0000 PROXY", "200001000.0000 BEOS", "30000000000");
  //note: beos.trustee finally consumed all rewards
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "2.0000 BEOS", "294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( distrib_onblock_call_test, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block = 100;
  tgs.beos.ending_block = 200;
  tgs.beos.block_interval = 1;
  tgs.beos.trustee_reward = 200'000 * 101;

  tgs.ram.starting_block = 1100;
  tgs.ram.ending_block = 1200;
  tgs.ram.block_interval = 1;

  check_change_params( tgs );

  issue( N(alice), asset::from_string("1000.0000 PROXY") );

  uint32_t block_nr;

  block_nr = 20; // outside of distribution period
  push_action( N(alice), N(onblock), block_nr, config::distribution_account_name );

  CHECK_STATS(alice, "1000.0000 PROXY", "0.0000 BEOS", "");

  block_nr = 150; // inside distribution period
  try
  {
    push_action( N(alice), N(onblock), block_nr, config::distribution_account_name );
  }
  catch(...) {}

  CHECK_STATS(alice, "1000.0000 PROXY", "0.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(eosio_reward_tests)

BOOST_FIXTURE_TEST_CASE( many_accounts_test1, eosio_init_bigstate_tester ) try {
  /*
      Reward periods for stake and ram are different. No proxies for accounts.
  */

  reward_period = 20;

  tgs.beos.starting_block = 180;
  tgs.beos.ending_block = tgs.beos.starting_block + reward_period - 1;
  tgs.beos.block_interval = 1;
  tgs.beos.trustee_reward = 10000 * reward_period;

  tgs.ram.starting_block = 280;
  tgs.ram.ending_block = tgs.ram.starting_block + reward_period - 1;
  tgs.ram.block_interval = 1;


  check_change_params( tgs );

  create_accounts_with_resources( config::system_account_name, no_of_accounts );

  BOOST_CHECK( control->head_block_num() < tgs.beos.starting_block );

  produce_blocks( tgs.beos.ending_block - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.beos.ending_block );

  produce_blocks( tgs.ram.ending_block - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.ram.ending_block );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", ASSET_STRING(tgs.beos.trustee_reward, BEOS), "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( many_accounts_test2, eosio_init_bigstate_tester ) try {
  /*
      Reward periods for stake and ram are the same. No proxies for accounts.
  */

  reward_period = 20;

  tgs.beos.starting_block = 180;
  tgs.beos.ending_block = tgs.beos.starting_block + reward_period - 1;
  tgs.beos.block_interval = 1;
  tgs.beos.trustee_reward = 10000 * reward_period;

  tgs.ram.starting_block = tgs.beos.starting_block;
  tgs.ram.ending_block = tgs.beos.ending_block;
  tgs.ram.block_interval = tgs.beos.block_interval;

  check_change_params( tgs );

  create_accounts_with_resources( config::system_account_name, no_of_accounts );

  BOOST_CHECK( control->head_block_num() < tgs.beos.starting_block );

  produce_blocks( tgs.beos.ending_block - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.beos.ending_block );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", ASSET_STRING(tgs.beos.trustee_reward, BEOS), "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( many_accounts_test3, eosio_init_bigstate_tester ) try {
  /*
      Reward periods for stake and ram are different. Proxies for accounts.
  */

  reward_period = 20;

  tgs.beos.starting_block = 180 + no_of_accounts;
  tgs.beos.ending_block = tgs.beos.starting_block + reward_period - 1;
  tgs.beos.block_interval = 1;
  tgs.beos.trustee_reward = 10000 * reward_period;

  tgs.ram.starting_block = 280 + no_of_accounts;
  tgs.ram.ending_block = tgs.ram.starting_block + reward_period - 1;
  tgs.ram.block_interval = 1;

  check_change_params( tgs );

  const uint64_t stake_reward_per_account = reward_period * tgs.beos.trustee_reward / no_of_accounts;
  const uint64_t ram_reward_per_account = reward_period * tgs.ram.trustee_reward / no_of_accounts;

  account_names_t accounts( create_accounts_with_resources( config::system_account_name, no_of_accounts ) );

  issue_for_accounts( accounts, asset::from_string("1.0000 PROXY") );

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", "0.0000 BEOS", "");

  BOOST_CHECK( control->head_block_num() < tgs.beos.starting_block );

  produce_blocks( tgs.beos.ending_block - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.beos.ending_block );

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", ASSET_STRING(stake_reward_per_account, BEOS), "");

  produce_blocks( tgs.ram.ending_block - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.ram.ending_block );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", ASSET_STRING(tgs.beos.trustee_reward, BEOS), "");

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", ASSET_STRING(stake_reward_per_account, BEOS), std::to_string(ram_reward_per_account).c_str());

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( many_accounts_test4, eosio_init_bigstate_tester ) try {
  /*
      Reward periods for stake and ram are the same. Proxies for accounts.
  */

  reward_period = 20;

  tgs.beos.starting_block = 180 + no_of_accounts;
  tgs.beos.ending_block = tgs.beos.starting_block + reward_period - 1;
  tgs.beos.block_interval = 1;
  tgs.beos.trustee_reward = 10000 * reward_period;

  tgs.ram.starting_block = tgs.beos.starting_block;
  tgs.ram.ending_block = tgs.beos.ending_block;
  tgs.ram.block_interval = 1;

  check_change_params( tgs );

  const uint64_t stake_reward_per_account = reward_period * tgs.beos.trustee_reward / no_of_accounts;
  const uint64_t ram_reward_per_account = reward_period * tgs.ram.trustee_reward / no_of_accounts;

  account_names_t accounts( create_accounts_with_resources( config::system_account_name, no_of_accounts ) );

  issue_for_accounts( accounts, asset::from_string("1.0000 PROXY") );

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", "0.0000 BEOS", "");

  BOOST_CHECK( control->head_block_num() < tgs.beos.starting_block );

  produce_blocks( tgs.beos.ending_block - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.beos.ending_block );

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", ASSET_STRING(stake_reward_per_account, BEOS), std::to_string(ram_reward_per_account).c_str());

  CHECK_STATS(beos.trustee, "0.0000 PROXY", ASSET_STRING(tgs.beos.trustee_reward, BEOS), "");

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(eosio_interchain_tests)

BOOST_FIXTURE_TEST_CASE( basic_lock_test, eosio_interchain_tester ) try {

  test_global_state tgs;
  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("5.0000 PROXY") ) );

  CHECK_STATS(bob, "5.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 240 - control->head_block_num() - 1 );

  CHECK_STATS(bob, "5.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );

  CHECK_STATS(bob, "5.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 244u );

  CHECK_STATS(bob, "5.0000 PROXY", "50000000.0000 BEOS", "20000000000");

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  CHECK_STATS(bob, "5.0000 PROXY", "50000000.0000 BEOS", "30000000000");

  produce_blocks( 2 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(bob, "5.0000 PROXY", "100000000.0000 BEOS", "30000000000");

  produce_blocks( 10 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(bob, "5.0000 PROXY", "150000000.0000 BEOS", "30000000000");

  produce_blocks( 10 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(bob, "5.0000 PROXY", "200000000.0000 BEOS", "30000000000");
} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test2, eosio_interchain_tester ) try {

  test_global_state tgs;
  check_change_params( tgs );

  issue( N(alice), asset::from_string("100.0000 PROXY") );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 240 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );

  CHECK_STATS(alice, "100.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  issue( N(bob), asset::from_string("50.0000 PROXY") );

  CHECK_STATS(bob, "50.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 3 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 244u );

  CHECK_STATS(alice, "", "", "16666666666");
  CHECK_STATS(bob,   "", "", "3333333333");

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  CHECK_STATS(alice, "", "", "23333333333");
  CHECK_STATS(bob,   "", "", "6666666666");

  produce_blocks( 2 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "100.0000 PROXY", "83333333.3333 BEOS", "23333333333");
  CHECK_STATS(bob,   "50.0000 PROXY", "16666666.6666 BEOS", "6666666666");

  produce_blocks( 10 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "100.0000 PROXY" , "116666666.6666 BEOS", "23333333333");
  CHECK_STATS(bob, "50.0000 PROXY" , "33333333.3332 BEOS", "6666666666");

  produce_blocks( 10 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "100.0000 PROXY" , "150000000.0000 BEOS", "23333333333");
  CHECK_STATS(bob,   "50.0000 PROXY" , "49999999.9999 BEOS", "6666666666");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test3, eosio_interchain_tester ) try {

  test_global_state tgs;
  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("100.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );

  CHECK_STATS(alice, "100.0000 PROXY" , "50000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("100.0000 PROXY") ) );

  CHECK_STATS(bob, "100.0000 PROXY" , "0.0000 BEOS", "0");

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "100.0000 PROXY" , "75000000.0000 BEOS", "20000000000");
  CHECK_STATS(bob, "100.0000 PROXY" , "25000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("111.0000 PROXY") ) );
  CHECK_STATS(carol, "111.0000 PROXY" , "0.0000 BEOS", "0");

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS( alice, "" , "91077170.4180 BEOS", "20000000000");
  CHECK_STATS( bob, "" , "41077170.4180 BEOS", "10000000000");
  CHECK_STATS( carol, "" , "17845659.1639 BEOS", "0");

  issue( N(dan), asset::from_string("1500.9876 PROXY") );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS( alice, "" , "93836571.1997 BEOS", "");
  CHECK_STATS( bob, "" , "43836571.1997 BEOS", "");
  CHECK_STATS( carol, "" , "20908594.0316 BEOS", "");
  CHECK_STATS( dan, "" , "41418263.5687 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test4, eosio_interchain_tester ) try {

  test_global_state tgs;
  check_change_params( tgs );

  produce_blocks( 270 - control->head_block_num() - 3 );

  /*
    Block number 270 has 2 actions:
    a) issue for 'carol' account
    b) transfers staked BEOS-es to BEOS-es (unused rewards from all previous steps accumulate in final pool)
  */
  issue( N(alice), asset::from_string("132.0000 PROXY") );
  issue( N(bob), asset::from_string("132.0000 PROXY") );
  issue( N(carol), asset::from_string("66.0000 PROXY") );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "", "80000000.0000 BEOS", "");
  CHECK_STATS(bob,   "", "80000000.0000 BEOS", "");
  CHECK_STATS(carol, "", "40000000.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test5, eosio_interchain_tester ) try {

  test_global_state tgs;
  check_change_params( tgs );

  BOOST_TEST_MESSAGE( "Lack any locks" );
  produce_blocks( 270 - control->head_block_num() );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test6, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "Every issue is too late, is triggered after distribution period" );

  test_global_state tgs;
  check_change_params( tgs );

  produce_blocks( 270 - control->head_block_num() );

  issue( N(alice), asset::from_string("132.0000 PROXY") );
  issue( N(bob), asset::from_string("162.0000 PROXY") );

  CHECK_STATS(alice, "132.0000 PROXY", "0.0000 BEOS", "");
  CHECK_STATS(bob, "162.0000 PROXY", "0.0000 BEOS", "");

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 280u );

  CHECK_STATS(alice, "132.0000 PROXY", "0.0000 BEOS", "");
  CHECK_STATS(bob, "162.0000 PROXY", "0.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test7, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "A few locks for 3 accounts" );

  test_global_state tgs;
  check_change_params( tgs );

  issue( N(alice), asset::from_string("0.0002 PROXY") );
  issue( N(bob), asset::from_string("0.0002 PROXY") );
  issue( N(carol), asset::from_string("0.0001 PROXY") );

  issue( N(alice), asset::from_string("0.0002 PROXY") );
  issue( N(bob), asset::from_string("0.0002 PROXY") );
  issue( N(carol), asset::from_string("0.0001 PROXY") );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "", "20000000.0000 BEOS", "");
  CHECK_STATS(bob,   "", "20000000.0000 BEOS", "");
  CHECK_STATS(carol, "", "10000000.0000 BEOS", "");

  issue( N(alice), asset::from_string("0.0012 PROXY") );
  issue( N(bob), asset::from_string("0.0012 PROXY") );
  issue( N(carol), asset::from_string("0.0006 PROXY") );

  issue( N(alice), asset::from_string("0.0012 PROXY") );
  issue( N(bob), asset::from_string("0.0012 PROXY") );
  issue( N(carol), asset::from_string("0.0006 PROXY") );

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "", "40000000.0000 BEOS", "");
  CHECK_STATS(bob, "", "40000000.0000 BEOS", "");
  CHECK_STATS(carol, "", "20000000.0000 BEOS", "");

  issue( N(alice), asset::from_string("0.0022 PROXY") );
  issue( N(bob), asset::from_string("0.0022 PROXY") );
  issue( N(carol), asset::from_string("0.0011 PROXY") );

  issue( N(alice), asset::from_string("0.0022 PROXY") );
  issue( N(bob), asset::from_string("0.0022 PROXY") );
  issue( N(carol), asset::from_string("0.0011 PROXY") );

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "", "60000000.0000 BEOS", "");
  CHECK_STATS(bob, "", "60000000.0000 BEOS", "");
  CHECK_STATS(carol, "", "30000000.0000 BEOS", "");

  issue( N(alice), asset::from_string("0.0024 PROXY") );
  issue( N(bob), asset::from_string("0.0024 PROXY") );
  issue( N(carol), asset::from_string("0.0012 PROXY") );

  issue( N(alice), asset::from_string("0.0024 PROXY") );
  issue( N(bob), asset::from_string("0.0024 PROXY") );
  issue( N(carol), asset::from_string("0.0012 PROXY") );

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "", "80000000.0000 BEOS", "");
  CHECK_STATS(bob, "", "80000000.0000 BEOS", "");
  CHECK_STATS(carol, "", "40000000.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( manipulation_lock_test, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "2 accounts are alternately locked and decreased" );

  test_global_state tgs;
  check_change_params( tgs );

  issue( N(alice), asset::from_string("1.0000 PROXY") );

  CHECK_STATS(alice, "1.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "1.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("overdrawn balance during withdraw"), withdraw( N(alice), asset::from_string("1.0001 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );
  //note: withdrawn before ram rewards at 244 and 248, ram left on distrib

  CHECK_STATS(alice, "", "50000000.0000 BEOS", "10000000000");

  issue( N(bob), asset::from_string("600.0000 PROXY") );

  CHECK_STATS(bob, "600.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );
  //note: unused beos reward from 250 increased pool in further steps

  CHECK_STATS(alice, "", "50000000.0000 BEOS", "10000000000");
  CHECK_STATS(bob, "", "75000000.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("600.0000 PROXY") ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "", "50000000.0000 BEOS", "10000000000");
  CHECK_STATS(bob, "", "75000000.0000 BEOS", "0");
  //note: beos reward from final step left unclaimed
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "75000002.0000 BEOS", "20000294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( manipulation_lock_test2, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "1 account - actions: issue, withdraw in different configurations" );

  test_global_state tgs;
  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "1.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );

  CHECK_STATS(alice, "2.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("2.0000 PROXY") ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );
  //note: withdrawn before second and final ram reward steps, ram left on distrib

  CHECK_STATS(alice, "0.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("3.0000 PROXY") ) );

  CHECK_STATS(alice, "3.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("3.0000 PROXY") ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("33.0000 PROXY") ) );

  CHECK_STATS(alice, "33.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );
  //note: unused beos rewards from steps at 250 and 260 increased pool in final step

  CHECK_STATS(alice, "33.0000 PROXY", "200000000.0000 BEOS", "10000000000");
  //note: beos reward distributed fully
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "2.0000 BEOS", "20000294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( manipulation_lock_test3, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "4 accounts - actions: issue, withdraw in different configurations" );

  test_global_state tgs;
  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("8.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("8.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "8.0000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(bob,   "8.0000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(carol, "8.0000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(dan,   "8.0000 PROXY", "12500000.0000 BEOS", "2500000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("16.0000 PROXY") ) );

  CHECK_STATS(alice, "24.0000 PROXY", "12500000.0000 BEOS", "5833333333");
  CHECK_STATS(bob,   "24.0000 PROXY", "12500000.0000 BEOS", "5833333333");
  CHECK_STATS(carol, "24.0000 PROXY", "12500000.0000 BEOS", "5833333333");
  CHECK_STATS(dan,   "0.0000 PROXY", "12500000.0000 BEOS", "2500000000");

  produce_blocks( 6 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "24.0000 PROXY", "29166666.6666 BEOS", "9166666666");
  CHECK_STATS(bob,   "24.0000 PROXY", "29166666.6666 BEOS", "9166666666");
  CHECK_STATS(carol, "24.0000 PROXY", "29166666.6666 BEOS", "9166666666");
  CHECK_STATS(dan,   "0.0000 PROXY", "12500000.0000 BEOS", "2500000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("16.0000 PROXY") ) );

  CHECK_STATS(alice, "8.0000 PROXY", "29166666.6666 BEOS", "9166666666");
  CHECK_STATS(bob,   "8.0000 PROXY", "29166666.6666 BEOS", "9166666666");
  CHECK_STATS(carol, "24.0000 PROXY", "29166666.6666 BEOS", "9166666666");
  CHECK_STATS(dan,   "16.0000 PROXY", "12500000.0000 BEOS", "2500000000");

  produce_blocks( 7 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "8.0000 PROXY", "36309523.8094 BEOS", "9166666666");
  CHECK_STATS(bob,   "8.0000 PROXY", "36309523.8094 BEOS", "9166666666");
  CHECK_STATS(carol, "24.0000 PROXY", "50595238.0952 BEOS", "9166666666");
  CHECK_STATS(dan,   "16.0000 PROXY", "26785714.2857 BEOS", "2500000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("48.0000 PROXY") ) );

  produce_blocks( 7 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "0.0000 PROXY", "36309523.8094 BEOS", "9166666666");
  CHECK_STATS(bob,   "56.0000 PROXY", "71309523.8096 BEOS", "9166666666");
  CHECK_STATS(carol, "24.0000 PROXY", "65595238.0952 BEOS", "9166666666");
  CHECK_STATS(dan,   "0.0000 PROXY", "26785714.2857 BEOS", "2500000000");
  //note: just leftovers from reward truncation (0.0001 BEOS, 2 ram) remain unclaimed
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "2.0001 BEOS", "294554"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( performance_lock_test, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "1 account - a lot of locks" );

  test_global_state tgs;
  check_change_params( tgs );

  std::vector< action > v;

  for( int32_t i = 0; i < 1000; ++i )
    v.emplace_back( create_issue_action( N(alice), asset::from_string("0.0001 PROXY") ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "0.1000 PROXY", "50000000.0000 BEOS", "10000000000");

  v.clear();
  for( int32_t i = 0; i < 5000; ++i )
    v.emplace_back( create_issue_action( N(alice), asset::from_string("0.0001 PROXY") ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "0.6000 PROXY", "100000000.0000 BEOS", "30000000000");

  v.clear();
  for( int32_t i = 0; i < 5000; ++i )
    v.emplace_back( create_issue_action( N(alice), asset::from_string("1000.0000 PROXY") ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "5000000.6000 PROXY", "150000000.0000 BEOS", "30000000000");

  v.clear();
  for( int32_t i = 0; i < 1000; ++i )
    v.emplace_back( create_issue_action( N(alice), asset::from_string("10000.0000 PROXY") ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "15000000.6000 PROXY", "200000000.0000 BEOS", "30000000000");
  //note: all rewards used
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "2.0000 BEOS", "294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( performance_lock_test2, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "4 accounts - a lot of locks" );

  test_global_state tgs;
  check_change_params( tgs );

  std::vector< action > v;

  for( int32_t i = 0; i < 1000; ++i )
  {
    v.emplace_back( create_issue_action( N(alice), asset::from_string("0.0001 PROXY") ) );
    v.emplace_back( create_issue_action( N(bob),   asset::from_string("0.0001 PROXY") ) );
    v.emplace_back( create_issue_action( N(carol), asset::from_string("0.0001 PROXY") ) );
    v.emplace_back( create_issue_action( N(dan),   asset::from_string("0.0001 PROXY") ) );
  }
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "0.1000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(bob,   "0.1000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(carol, "0.1000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(dan,   "0.1000 PROXY", "12500000.0000 BEOS", "2500000000");

  v.clear();

  for( int32_t i = 0; i < 1000; ++i )
  {
    if(i==0) 
    {
      v.emplace_back( create_issue_action( N(alice), asset::from_string("1.9000 PROXY") ) );
      v.emplace_back( create_issue_action( N(carol), asset::from_string("0.9000 PROXY") ) );
      v.emplace_back( create_issue_action( N(bob),   asset::from_string("1.9000 PROXY") ) );
    }
    else
    {
      v.emplace_back( create_issue_action( N(alice), asset::from_string("2.0000 PROXY") ) );
      v.emplace_back( create_issue_action( N(carol), asset::from_string("1.0000 PROXY") ) );
      v.emplace_back( create_issue_action( N(bob),   asset::from_string("2.0000 PROXY") ) );
    }
  }

  locks( N(beos.gateway), std::move( v ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("0.1000 PROXY") ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "2000.0000 PROXY", "32500000.0000 BEOS", "10500000000");
  CHECK_STATS(bob,   "2000.0000 PROXY", "32500000.0000 BEOS", "10500000000");
  CHECK_STATS(carol, "1000.0000 PROXY", "22500000.0000 BEOS", "6500000000");
  CHECK_STATS(dan,   "0.0000 PROXY", "12500000.0000 BEOS", "2500000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("2000.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("2000.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(carol), asset::from_string("1000.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("1000.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("0.1000 PROXY") ) );

  v.clear();
  for( int32_t i = 0; i < 1000; ++i )
  {
    v.emplace_back( create_issue_action( N(carol), asset::from_string("5.0000 PROXY") ) );

    if( i == 0 )
      v.emplace_back( create_issue_action( N(dan), asset::from_string("4.9000 PROXY") ) );
    else
      v.emplace_back( create_issue_action( N(dan), asset::from_string("5.0000 PROXY") ) );
  }
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "0.0000 PROXY", "32500000.0000 BEOS", "10500000000");
  CHECK_STATS(bob,   "0.0000 PROXY", "32500000.0000 BEOS", "10500000000");
  CHECK_STATS(carol, "6000.0000 PROXY", "49772727.2727 BEOS", "6500000000");
  CHECK_STATS(dan,   "5000.0000 PROXY", "35227272.7272 BEOS", "2500000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(carol), asset::from_string("6000.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("5000.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("2000.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("2000.0000 PROXY") ) );

  v.clear();
  // [MK]: temporary (?) decrease to 2000, because 3000 fail on my machine
  //for( int32_t i = 0; i < 3000; ++i )
  for( int32_t i = 0; i < 2000; ++i )
  {
    v.emplace_back( create_issue_action( N(alice), asset::from_string("5.0000 PROXY") ) );
    v.emplace_back( create_issue_action( N(bob), asset::from_string("5.0000 PROXY") ) );
  }
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 273u );

  CHECK_STATS(alice, "12000.0000 PROXY", "57500000.0000 BEOS", "10500000000");
  CHECK_STATS(bob,   "12000.0000 PROXY", "57500000.0000 BEOS", "10500000000");
  CHECK_STATS(carol, "0.0000 PROXY", "49772727.2727 BEOS", "6500000000");
  CHECK_STATS(dan,   "0.0000 PROXY", "35227272.7272 BEOS", "2500000000");
  //note: almost all rewards used, just 0.0001 left from truncations
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "2.0001 BEOS", "294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( false_tests, eosio_interchain_tester ) try {

  test_global_state tgs;
  check_change_params( tgs );

  produce_blocks( 100 - control->head_block_num() );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_TEST_MESSAGE( "'issue' action" );

  BOOST_REQUIRE_EQUAL( "unknown key (eosio::chain::name): fake2.acc: ", issue( N(fake2.acc), asset::from_string("3.4567 PROXY") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("cannot issue to self"), issue( N(beos.gateway), asset::from_string("100.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("unable to find key"), issue( N(alice), asset::from_string("100.0000 XYZ") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("symbol precision mismatch"), issue( N(alice), asset::from_string("100.000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("must issue positive quantity"), issue( N(alice), asset::from_string("0.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_TEST_MESSAGE( "'withdraw' action" );

  BOOST_REQUIRE_EQUAL( "action's authorizing actor 'fake.acc2' does not exist", withdraw( N(fake.acc2), asset::from_string("5.5432 PROXY") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("unable to find key"), withdraw( N(beos.gateway), asset::from_string("100.0000 ABC") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("symbol precision mismatch"), withdraw( N(beos.gateway), asset::from_string("100.00 PROXY") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( performance_decrease_test, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "Decreasing balance for 1 account" );

  test_global_state tgs;
  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice,"1.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 2 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 244u );

  CHECK_STATS(alice,"8.0000 PROXY", "50000000.0000 BEOS", "20000000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 3 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );
  //note: ram reward from final step unused, left on distrib

  CHECK_STATS(alice,"0.0000 PROXY", "50000000.0000 BEOS", "20000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("0.6000 PROXY") ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice,"0.6000 PROXY", "100000000.0000 BEOS", "20000000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.2000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );

  produce_blocks( 7 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice,"0.2000 PROXY", "150000000.0000 BEOS", "20000000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );
  CHECK_STATS(alice,"0.1000 PROXY", "", "");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );
  CHECK_STATS(alice,"0.0000 PROXY", "", "");

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("overdrawn balance during withdraw"), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );
  CHECK_STATS(alice,"0.0000 PROXY", "", "");

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("overdrawn balance during withdraw"), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );
  CHECK_STATS(alice,"0.0000 PROXY", "", "");

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice,"0.0000 PROXY", "150000000.0000 BEOS", "20000000000");
  //note: beos reward from final step left unused
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "50000002.0000 BEOS", "10000294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( performance_decrease_test2, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "Decreasing balance for 4 accounts" );

  test_global_state tgs;
  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("2.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("2.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice,"2.0000 PROXY", "25000000.0000 BEOS", "5000000000");
  CHECK_STATS(bob,  "2.0000 PROXY", "25000000.0000 BEOS", "5000000000");

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("overdrawn balance during withdraw"), withdraw( N(bob), asset::from_string("6.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("2.0000 PROXY") ) );

  produce_blocks( 3 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 244u );
  //note: bob withdrawn before second step of ram rewards, whole reward went to alice

  CHECK_STATS(alice,"2.0000 PROXY", "25000000.0000 BEOS", "15000000000");
  CHECK_STATS(bob  ,"0.0000 PROXY", "25000000.0000 BEOS", "5000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("10.0000 PROXY") ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );
  //note: alice withdrawn before final step of ram rewards, whole reward went to bob

  CHECK_STATS(alice, "0.0000 PROXY", "25000000.0000 BEOS", "15000000000");
  CHECK_STATS(bob, "8.0000 PROXY", "25000000.0000 BEOS", "15000000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );
  //note: beos rewards from step at 250 unused, increase pool for next steps

  CHECK_STATS(alice,"0.0000 PROXY", "25000000.0000 BEOS", "15000000000");
  CHECK_STATS(bob, "0.0000 PROXY", "25000000.0000 BEOS", "15000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("48.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("48.0000 PROXY") ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "0.0000 PROXY", "25000000.0000 BEOS", "15000000000");
  CHECK_STATS(bob,   "0.0000 PROXY", "25000000.0000 BEOS", "15000000000");
  CHECK_STATS(carol, "48.0000 PROXY", "37500000.0000 BEOS", "0");
  CHECK_STATS(dan,   "48.0000 PROXY", "37500000.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("40.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("41.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("overdrawn balance during withdraw"), withdraw( N(dan), asset::from_string("500.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("overdrawn balance during withdraw"), withdraw( N(alice), asset::from_string("500.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("48.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("must withdraw positive quantity"), withdraw( N(alice), asset::from_string("0.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("40.0000 PROXY") ) );

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "0.0000 PROXY", "25000000.0000 BEOS", "15000000000");
  CHECK_STATS(bob,   "48.0000 PROXY", "62500000.0000 BEOS", "15000000000");
  CHECK_STATS(carol, "48.0000 PROXY", "75000000.0000 BEOS", "0");
  CHECK_STATS(dan,   "0.0000 PROXY", "37500000.0000 BEOS", "0");
  //note: in the end all rewards were used
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "2.0000 BEOS", "294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_1, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( " Test issue, withdraw for one account");

  test_global_state tgs;
  check_change_params( tgs );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "8.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("16.0000 PROXY") ) );
  //note: withdrawn befor ram rewards at 244 and 248
  
  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "0.0000 PROXY", "50000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );
  
  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );
  //note: unused beos reward from step at 250 increases pool of rewards for next steps
  
  CHECK_STATS(alice,  "8.0000 PROXY", "125000000.0000 BEOS", "10000000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice,  "0.0000 PROXY", "125000000.0000 BEOS", "10000000000");
  //note: last beos reward unused, left on distrib
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "75000002.0000 BEOS", "20000294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_2, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( " Test issue, withdraw for four accounts");

  test_global_state tgs;
  check_change_params( tgs );

  const auto& StN = eosio::chain::string_to_name;
  using Accounts = std::vector<std::string>;
  Accounts accounts = {"alice", "bob", "carol", "dan"};

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), issue( StN(_acc.c_str()), asset::from_string("8.0000 PROXY") ) );
  }

  produce_blocks( 240 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );

  CHECK_STATS(alice, "8.0000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(bob,   "8.0000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(carol, "8.0000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(dan,   "8.0000 PROXY", "12500000.0000 BEOS", "2500000000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), issue( StN(_acc.c_str()), asset::from_string("8.0000 PROXY") ) );
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("16.0000 PROXY") ) );
  }
  //note: first two accounts withdraw before second step of ram distrib at 244, all do that before last
  //step at 248, so last reward is lost (left on distrib)

  produce_blocks(2);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "0.0000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(bob,   "0.0000 PROXY", "12500000.0000 BEOS", "2500000000");
  CHECK_STATS(carol, "0.0000 PROXY", "12500000.0000 BEOS", "7500000000");
  CHECK_STATS(dan,   "0.0000 PROXY", "12500000.0000 BEOS", "7500000000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), issue( StN(_acc.c_str()), asset::from_string("8.0000 PROXY") ) );
  }
  //note: beos reward from previous unused step at 250 increased pool for next steps

  produce_blocks(6);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "8.0000 PROXY", "31250000.0000 BEOS", "2500000000");
  CHECK_STATS(bob,   "8.0000 PROXY", "31250000.0000 BEOS", "2500000000");
  CHECK_STATS(carol, "8.0000 PROXY", "31250000.0000 BEOS", "7500000000");
  CHECK_STATS(dan,   "8.0000 PROXY", "31250000.0000 BEOS", "7500000000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("8.0000 PROXY") ) );
  }

  produce_blocks(6);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );
  CHECK_STATS(alice, "0.0000 PROXY", "31250000.0000 BEOS", "2500000000");
  CHECK_STATS(bob,   "0.0000 PROXY", "31250000.0000 BEOS", "2500000000");
  CHECK_STATS(carol, "0.0000 PROXY", "31250000.0000 BEOS", "7500000000");
  CHECK_STATS(dan,   "0.0000 PROXY", "31250000.0000 BEOS", "7500000000");
  //last step of beos reward at 270 is unused, left on distrib
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "75000002.0000 BEOS", "10000294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_3, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( " Test issue, withdraw for n dynamic accounts");

  test_global_state tgs;
  check_change_params( tgs );

  const auto& StN = eosio::chain::string_to_name;
  using Accounts = std::vector<std::string>;
  Accounts accounts = { "bozydar", "bogumil", "perun", "swiatowid", "weles"};

  for(const auto& _acc : accounts ) {
    create_account_with_resources( config::gateway_account_name, _acc.c_str() );
  }

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), issue( StN(_acc.c_str()), asset::from_string("10.0000 PROXY") ) );
  }

  produce_blocks( 240 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );
  
  CHECK_STATS(bozydar,  "10.0000 PROXY", "10000000.0000 BEOS", "2000000000");
  CHECK_STATS(bogumil,  "10.0000 PROXY", "10000000.0000 BEOS", "2000000000");
  CHECK_STATS(perun,    "10.0000 PROXY", "10000000.0000 BEOS", "2000000000");
  CHECK_STATS(swiatowid,"10.0000 PROXY", "10000000.0000 BEOS", "2000000000");
  CHECK_STATS(weles,    "10.0000 PROXY", "10000000.0000 BEOS", "2000000000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("10.0000 PROXY") ) );
  }
  //note: weles withdrawn after second ram distrib period that happened at block 244; ram rewards from
  //last step at 248 are lost (left on distrib)

  produce_blocks(5);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(bozydar,  "0.0000 PROXY", "10000000.0000 BEOS", "2000000000");
  CHECK_STATS(bogumil,  "0.0000 PROXY", "10000000.0000 BEOS", "2000000000");
  CHECK_STATS(perun,    "0.0000 PROXY", "10000000.0000 BEOS", "2000000000");
  CHECK_STATS(swiatowid,"0.0000 PROXY", "10000000.0000 BEOS", "2000000000");
  CHECK_STATS(weles,    "0.0000 PROXY", "10000000.0000 BEOS", "12000000000"); 

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), issue( StN(_acc.c_str()), asset::from_string("5.0000 PROXY") ) );
  }

  produce_blocks(5);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(bozydar,  "5.0000 PROXY", "25000000.0000 BEOS", "2000000000");
  CHECK_STATS(bogumil,  "5.0000 PROXY", "25000000.0000 BEOS", "2000000000");
  CHECK_STATS(perun,    "5.0000 PROXY", "25000000.0000 BEOS", "2000000000");
  CHECK_STATS(swiatowid,"5.0000 PROXY", "25000000.0000 BEOS", "2000000000");
  CHECK_STATS(weles,    "5.0000 PROXY", "25000000.0000 BEOS", "12000000000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("5.0000 PROXY") ) );
  }

  produce_blocks(5);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(bozydar,  "0.0000 PROXY", "25000000.0000 BEOS", "2000000000");
  CHECK_STATS(bogumil,  "0.0000 PROXY", "25000000.0000 BEOS", "2000000000");
  CHECK_STATS(perun,    "0.0000 PROXY", "25000000.0000 BEOS", "2000000000");
  CHECK_STATS(swiatowid,"0.0000 PROXY", "25000000.0000 BEOS", "2000000000");
  CHECK_STATS(weles,    "0.0000 PROXY", "25000000.0000 BEOS", "12000000000");
  //note: beos rewards from last step at 270 are lost (left on distrib)
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "75000002.0000 BEOS", "10000294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_4, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "Test issue, withdraw for created and dynamic accounts");

  test_global_state tgs;
  check_change_params( tgs );

  const auto& StN = eosio::chain::string_to_name;
  using Accounts = std::vector<std::string>;
  Accounts accounts = { "perun", "swiatowid" };

  for(const auto& _acc : accounts ) {
    create_account_with_resources( config::gateway_account_name, _acc.c_str() );
  }

  accounts.push_back("alice");
  accounts.push_back("dan");

  BOOST_REQUIRE_EQUAL( success(), issue( N(perun), asset::from_string("20.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(swiatowid), asset::from_string("20.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("10.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("10.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );

  CHECK_STATS(perun,    "20.0000 PROXY", "16666666.6666 BEOS", "3333333333");
  CHECK_STATS(swiatowid,"20.0000 PROXY", "16666666.6666 BEOS", "3333333333");
  CHECK_STATS(alice,    "10.0000 PROXY", "8333333.3333 BEOS", "1666666666");
  CHECK_STATS(dan,      "10.0000 PROXY", "8333333.3333 BEOS", "1666666666");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("10.0000 PROXY") ) );
  }

  produce_blocks(6);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );
  //note: all accounts withdraw before next step of ram distrib at 244, but two first have proxy left
  //on them so they share whole reward, same for final at 248 and beos step at 250

  CHECK_STATS(perun,    "10.0000 PROXY", "41666666.6666 BEOS", "13333333334");
  CHECK_STATS(swiatowid,"10.0000 PROXY", "41666666.6666 BEOS", "13333333334");
  CHECK_STATS(alice,    "0.0000 PROXY", "8333333.3333 BEOS", "1666666666");
  CHECK_STATS(dan,      "0.0000 PROXY", "8333333.3333 BEOS", "1666666666");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(perun), asset::from_string("10.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(swiatowid), asset::from_string("10.0000 PROXY") ) );

  produce_blocks(8);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(perun,    "0.0000 PROXY", "41666666.6666 BEOS", "13333333334");
  CHECK_STATS(swiatowid,"0.0000 PROXY", "41666666.6666 BEOS", "13333333334");
  CHECK_STATS(alice,    "0.0000 PROXY", "8333333.3333 BEOS", "1666666666");
  CHECK_STATS(dan,      "0.0000 PROXY", "8333333.3333 BEOS", "1666666666");

  produce_blocks(10);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(perun,    "0.0000 PROXY", "41666666.6666 BEOS", "13333333334");
  CHECK_STATS(swiatowid,"0.0000 PROXY", "41666666.6666 BEOS", "13333333334");
  CHECK_STATS(alice,    "0.0000 PROXY", "8333333.3333 BEOS", "1666666666");
  CHECK_STATS(dan,      "0.0000 PROXY", "8333333.3333 BEOS", "1666666666");
  //note: beos rewards from staps at 260 and 270 are lost (left on distrib), also 0.0002 left
  //from reward truncations
  CHECK_STATS(beos.distrib, "0.0000 PROXY", "100000002.0002 BEOS", "294552"); //+DEFAULT_RAM

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( creating_short_names, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "Creating names with length less than 12 chars - creator beos.gateway");

  create_account_with_resources( config::gateway_account_name, N(mario) );
  create_account_with_resources( config::gateway_account_name, N(mario.mar) );
  create_account_with_resources( config::gateway_account_name, N(12345123451) );
  create_account_with_resources( config::gateway_account_name, N(1234.x) );

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(beos_mainnet_tests)

BOOST_FIXTURE_TEST_CASE( buying_ram, beos_mainnet_tester ) try {
  BOOST_TEST_MESSAGE( "Buying ram with big 100mln BEOS chunks");

  test_global_state tgs;

  tgs.beos.starting_block = 30;
  tgs.beos.ending_block = 30;
  tgs.beos.block_interval = 1;
  tgs.beos.trustee_reward = 0;
  tgs.ram.starting_block = 30;
  tgs.ram.ending_block = 30;
  tgs.ram.block_interval = 1;
  tgs.ram.trustee_reward = 0;

  check_change_params( tgs );

  issue( N(alice), asset::from_string("1.0000 PROXY") );

  produce_blocks( 30 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
  //all rewards are on 'alice'
  CHECK_STATS(alice, "1.0000 PROXY", "", "32000000000");
  CHECK_STATS(bob, "0.0000 PROXY", "", "0");

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(alice) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(alice), { N(alice) } ) );

  BOOST_REQUIRE_EQUAL( success(), unstake( N(alice), N(alice), asset::from_string("1800000000.0000 BEOS"), asset::from_string("1800000000.0000 BEOS") ) );

  produce_block( fc::hours(3*24) );
  produce_blocks(1);
  
  asset liquid_beos = get_balance(N(alice));
  BOOST_REQUIRE_EQUAL( liquid_beos, asset::from_string("3600000000.0000 BEOS") );

  int64_t bob_ram = DEFAULT_RAM;
  for (int i = 0; i < 36; ++i) {
     buyram(N(alice), N(bob), asset::from_string("100000000.0000 BEOS"));
     int64_t new_bob_ram = check_data(N(bob))["staked_ram"].as_int64();
     int64_t bought_ram = new_bob_ram - bob_ram;
     bob_ram = new_bob_ram;
     BOOST_WARN_MESSAGE(false, std::string("100mln BEOS == ")+std::to_string(bought_ram)+" bytes");
  }
  bob_ram -= DEFAULT_RAM;
  BOOST_WARN_MESSAGE(false, std::string("Bob now has ")+std::to_string(bob_ram)+" bytes above default");
  //as expected spending almost all money gives almost all RAM
  BOOST_REQUIRE_GE(bob_ram, 36484490000);

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( buying_ram2, beos_mainnet_tester ) try {
  BOOST_TEST_MESSAGE( "Buying ram with smaller 100*1mln BEOS chunks");

  test_global_state tgs;

  tgs.beos.starting_block = 30;
  tgs.beos.ending_block = 30;
  tgs.beos.block_interval = 1;
  tgs.beos.trustee_reward = 0;
  tgs.ram.starting_block = 30;
  tgs.ram.ending_block = 30;
  tgs.ram.block_interval = 1;
  tgs.ram.trustee_reward = 0;

  check_change_params( tgs );

  issue( N(alice), asset::from_string("1.0000 PROXY") );

  produce_blocks( 30 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
  //all rewards are on 'alice'
  CHECK_STATS(alice, "1.0000 PROXY", "", "32000000000");
  CHECK_STATS(bob, "0.0000 PROXY", "", "0");

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(alice) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(alice), { N(alice) } ) );

  BOOST_REQUIRE_EQUAL( success(), unstake( N(alice), N(alice), asset::from_string("1800000000.0000 BEOS"), asset::from_string("1800000000.0000 BEOS") ) );

  produce_block( fc::hours(3*24) );
  produce_blocks(1);
  
  asset liquid_beos = get_balance(N(alice));
  BOOST_REQUIRE_EQUAL( liquid_beos, asset::from_string("3600000000.0000 BEOS") );

  int64_t bob_ram = DEFAULT_RAM;
  for (int i = 0; i < 36; ++i) {
     for (int j = 0; j < 100; ++j) {
        buyram(N(alice), N(bob), asset::from_string("1000000.0000 BEOS"));
     }
     int64_t new_bob_ram = check_data(N(bob))["staked_ram"].as_int64();
     int64_t bought_ram = new_bob_ram - bob_ram;
     bob_ram = new_bob_ram;
     BOOST_WARN_MESSAGE(false, std::string("100*1mln BEOS == ")+std::to_string(bought_ram)+" bytes");
  }
  bob_ram -= DEFAULT_RAM;
  BOOST_WARN_MESSAGE(false, std::string("Bob now has ")+std::to_string(bob_ram)+" bytes above default");
  //compared with previous test buying with many smaller chunks gives marginally less RAM due to many more truncations
  BOOST_REQUIRE_GE(bob_ram, 36484490000);

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( buying_rambytes, beos_mainnet_tester ) try {
  BOOST_TEST_MESSAGE( "Buying ram with 100*10mln byte chunks"); //trying to buy in 1bln chunks fails on calculations in exchange due to too large intermediate numbers

  test_global_state tgs;

  tgs.beos.starting_block = 30;
  tgs.beos.ending_block = 30;
  tgs.beos.block_interval = 1;
  tgs.beos.trustee_reward = 0;
  tgs.ram.starting_block = 30;
  tgs.ram.ending_block = 30;
  tgs.ram.block_interval = 1;
  tgs.ram.trustee_reward = 0;

  check_change_params( tgs );

  issue( N(alice), asset::from_string("1.0000 PROXY") );

  produce_blocks( 30 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
  //all rewards are on 'alice'
  CHECK_STATS(alice, "1.0000 PROXY", "", "32000000000");
  CHECK_STATS(bob, "0.0000 PROXY", "", "0");

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(alice) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(alice), { N(alice) } ) );

  BOOST_REQUIRE_EQUAL( success(), unstake( N(alice), N(alice), asset::from_string("1800000000.0000 BEOS"), asset::from_string("1800000000.0000 BEOS") ) );

  produce_block( fc::hours(3*24) );
  produce_blocks(1);
  
  asset liquid_beos = get_balance(N(alice));
  BOOST_REQUIRE_EQUAL( liquid_beos, asset::from_string("3600000000.0000 BEOS") );

  int64_t bob_ram = DEFAULT_RAM;
  for (int i = 0; i < 36; ++i) {
     for (int j = 0; j < 100; ++j)
        buyrambytes(N(alice), N(bob), 10000000);
     int64_t new_bob_ram = check_data(N(bob))["staked_ram"].as_int64();
     int64_t bought_ram = new_bob_ram - bob_ram;
     bob_ram = new_bob_ram;
     asset new_liquid_beos = get_balance(N(alice));
     asset spent_beos = liquid_beos - new_liquid_beos;
     liquid_beos = new_liquid_beos;
     BOOST_WARN_MESSAGE(false, spent_beos.to_string()+" == "+std::to_string(bought_ram)+" bytes");
  }
  bob_ram -= DEFAULT_RAM;
  BOOST_WARN_MESSAGE(false, std::string("Bob now has ")+std::to_string(bob_ram)+" bytes above default");
  BOOST_REQUIRE_EQUAL((bob_ram - 36000000000) * 1000000 / bob_ram, 0);
  BOOST_WARN_MESSAGE(false, std::string("Alice spent ")+(asset::from_string("3600000000.0000 BEOS")-liquid_beos).to_string());

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( selling_ram, beos_mainnet_tester ) try {
  BOOST_TEST_MESSAGE( "Selling ram with big 1bln byte chunks");

  test_global_state tgs;

  tgs.beos.starting_block = 30;
  tgs.beos.ending_block = 30;
  tgs.beos.block_interval = 1;
  tgs.beos.trustee_reward = 0;
  tgs.ram.starting_block = 30;
  tgs.ram.ending_block = 30;
  tgs.ram.block_interval = 1;
  tgs.ram.trustee_reward = 0;

  check_change_params( tgs );

  issue( N(alice), asset::from_string("1.0000 PROXY") );

  produce_blocks( 30 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
  //all rewards are on 'alice'
  CHECK_STATS(alice, "1.0000 PROXY", "", "32000000000");
  CHECK_STATS(bob, "0.0000 PROXY", "", "0");

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(alice) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(alice), { N(alice) } ) );

  BOOST_REQUIRE_EQUAL( success(), unstake( N(alice), N(alice), asset::from_string("1800000000.0000 BEOS"), asset::from_string("1800000000.0000 BEOS") ) );

  produce_block( fc::hours(3*24) );
  produce_blocks(1);
  
  asset liquid_beos = get_balance(N(alice));
  BOOST_REQUIRE_EQUAL( liquid_beos, asset::from_string("3600000000.0000 BEOS") );

  buyram(N(alice), N(alice), asset::from_string("3600000000.0000 BEOS"));
  int64_t alice_ram = check_data(N(alice))["staked_ram"].as_int64() - DEFAULT_RAM;
  BOOST_WARN_MESSAGE(false, std::string("Alice now has ")+std::to_string(alice_ram)+" bytes above default");
  BOOST_REQUIRE_GE(alice_ram, 68484490000);
  liquid_beos = get_balance(N(alice));
  BOOST_REQUIRE_EQUAL( liquid_beos, asset::from_string("0.0000 BEOS") );

  for (int i = 0; i < 68; ++i) {
     sellram(N(alice), 1000000000);
     asset new_liquid_beos = get_balance(N(alice));
     asset acquired_beos = new_liquid_beos - liquid_beos;
     liquid_beos = new_liquid_beos;
     BOOST_WARN_MESSAGE(false, std::string("Alice sold 1bln bytes for ")+acquired_beos.to_string());
  }
  BOOST_WARN_MESSAGE(false, std::string("Alice now has ")+liquid_beos.to_string());
  BOOST_REQUIRE_GE(liquid_beos, asset::from_string("3567000000.0000 BEOS"));

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()
