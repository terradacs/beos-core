#include <boost/test/unit_test.hpp>
#include <eosio/testing/tester.hpp>
#include <eosio/chain/abi_serializer.hpp>
#include <eosio/chain/resource_limits.hpp>

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

  eosio_interchain_tester(uint64_t state_size = 1024*1024*8)
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
    produce_blocks( 1 );

    prepare_account( config::system_account_name, eosio_system_wast, eosio_system_abi, &system_abi_ser );
    prepare_account( N(beos.init), eosio_init_wast, eosio_init_abi, &beos_init_abi_ser );
    prepare_account( config::gateway_account_name, eosio_gateway_wast, eosio_gateway_abi, &beos_gateway_abi_ser );
    prepare_account( config::distribution_account_name, eosio_distribution_wast, eosio_distribution_abi, &beos_distrib_abi_ser );

    //BOOST_REQUIRE_EQUAL( success(), issue( config::system_account_name, asset::from_string("1000000000.0000 BEOS"), config::system_account_name ) );
    BOOST_REQUIRE_EQUAL( success(), push_action( config::system_account_name, N(initialissue),
                                                 mvo()
                                                   ( "quantity", initial_supply * 10000 )
                                                   ( "min_activated_stake_percent", min_activated_stake_percent ),
                                                 system_abi_ser,
                                                 config::system_account_name
                                               ));

    BOOST_REQUIRE_EQUAL( success(), initresource( config::gateway_account_name,
                                                    100'000'000,
                                                    asset::from_string("1000.0000 BEOS"),
                                                    asset::from_string("1000.0000 BEOS")
                                                  )
                        );
    BOOST_REQUIRE_EQUAL( success(), initresource( config::distribution_account_name,
                                                    33'000'000'000,
                                                    asset::from_string("100000000.0000 BEOS"),
                                                    asset::from_string("100000000.0000 BEOS")
                                                  )
                        );
    //ABW: problem - amount to be issued depends on amount needed to cover resources to be distributed, however these
    //parameters are set in each test separately, not to mention they are set after this code is run, so we need to
    //have enough resources to cover all tests (but in each case we will have extra liquid BEOS in eosio and undistributed
    //resources in beos.distrib)

    // [MK]: need to change creation with multisig
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

  action_result change_params( const test_global_state& tgs )
  {
    variants v;
    v.emplace_back( std::move( tgs.proxy_asset ) );
    v.emplace_back( tgs.starting_block_for_initial_witness_election );
    v.emplace_back( std::move( tgs.beos ) );
    v.emplace_back( std::move( tgs.ram ) );
    v.emplace_back( std::move( tgs.trustee ) );

    return push_action( N(beos.init), N(changeparams), mvo()
        ("new_params",     v),
        beos_init_abi_ser,
        N(beos.init)
      );
  }

protected:
  uint64_t  initial_supply = 1'000'000'000;
  uint8_t   min_activated_stake_percent = 15; // 15% is default in eosio

};

class eosio_init_tester: public eosio_interchain_tester
{
  public:
 
  eosio_init_tester(uint64_t state_size = 1024*1024*8)
    : eosio_interchain_tester(state_size) {}

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
    auto buffer1 = state.starting_block_for_distribution;
    state.starting_block_for_distribution = 0;
    BOOST_REQUIRE_EQUAL( wasm_assert_msg("STARTING_BLOCK_FOR_DISTRIBUTION > 0"), change_params( tgs ) );
    BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
    state.starting_block_for_distribution = buffer1;

    auto buffer2 = state.starting_block_for_distribution;
    auto buffer3 = state.ending_block_for_distribution;
    state.starting_block_for_distribution = 2;
    state.ending_block_for_distribution = 2;
    BOOST_REQUIRE_EQUAL( wasm_assert_msg("ENDING_BLOCK_FOR_DISTRIBUTION > STARTING_BLOCK_FOR_DISTRIBUTION"), change_params( tgs ) );
    BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );

    state.starting_block_for_distribution = 3;
    BOOST_REQUIRE_EQUAL( wasm_assert_msg("ENDING_BLOCK_FOR_DISTRIBUTION > STARTING_BLOCK_FOR_DISTRIBUTION"), change_params( tgs ) );
    BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
    state.starting_block_for_distribution = buffer2;
    state.ending_block_for_distribution = buffer3;

    state.starting_block_for_distribution = buffer2;
    state.ending_block_for_distribution = buffer3;
    auto buffer4 = state.distribution_payment_block_interval_for_distribution;
    state.distribution_payment_block_interval_for_distribution = 0;
    BOOST_REQUIRE_EQUAL( wasm_assert_msg("DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_DISTRIBUTION > 0"), change_params( tgs ) );
    BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
    state.distribution_payment_block_interval_for_distribution = buffer4;

    auto buffer5 = state.amount_of_reward;
    state.amount_of_reward = 0;
    BOOST_REQUIRE_EQUAL( wasm_assert_msg("AMOUNT_OF_REWARD > 0"), change_params( tgs ) );
    BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
    state.amount_of_reward = buffer5;
  }

};

/*
  Values of parameters for `eosio_init` contract.

  starting_block_for_initial_witness_election                 100

  starting_block_for_beos_distribution						            240
  ending_block_for_beos_distribution							            270
  distribution_payment_block_interval_for_beos_distribution	  10
  amount_of_reward_beos										                    800 * 10000

  starting_block_for_ram_distribution							            240
  ending_block_for_ram_distribution							              248
  distribution_payment_block_interval_for_ram_distribution	  4
  amount_of_reward_ram										                    500 * 10000
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

uint64_t eosio_init_bigstate_tester::state_size = 1 * 1024 * 1024 * 1024ll;
size_t eosio_init_bigstate_tester::no_of_accounts = 50'000; //< it passed succesfuly for 100k accounts and 1G state
const size_t eosio_init_bigstate_tester::actions_per_trx = 2000;

#define CHECK_STATS_(_accName, _expectedBalance, _expectedStakedBalance, _expectedStakedRam)  \
{                                                                                             \
    std::string _expectedStakedRam2 = _expectedStakedRam;                                     \
    if( _expectedStakedRam2.size() )                                                          \
    {                                                                                         \
      auto val = std::stol( _expectedStakedRam2 );                                            \
      _expectedStakedRam2 = std::to_string( DEFAULT_RAM + val );                              \
    }                                                                                         \
    auto stats = check_data( _accName );                                                      \
    const bool expected_balance_empty = strlen(_expectedBalance) == 0;                        \
    const bool expected_staked_balance_empty = strlen(_expectedStakedBalance) == 0;           \
    const bool expected_staked_ram_empty = _expectedStakedRam2.size() == 0 ;                  \
    if(!expected_balance_empty){                                                              \
      BOOST_REQUIRE_EQUAL( stats["balance"].as_string(), ( _expectedBalance ) );              \
    }                                                                                         \
    if(!expected_staked_balance_empty){                                                       \
      BOOST_REQUIRE_EQUAL( stats["staked_balance"].as_string(), ( _expectedStakedBalance ) ); \
    }                                                                                         \
    if(!expected_staked_ram_empty) {                                                          \
      BOOST_REQUIRE_EQUAL( stats["staked_ram"].as_string(), ( _expectedStakedRam2 ) );        \
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

BOOST_AUTO_TEST_SUITE(eosio_init_tests)

BOOST_FIXTURE_TEST_CASE( basic_param_test, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block_for_distribution = 100;
  tgs.beos.ending_block_for_distribution = 105;
  tgs.beos.distribution_payment_block_interval_for_distribution = 8;

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  issue( N(alice), asset::from_string("100.0000 PROXY") );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "");

  produce_blocks( 100 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  CHECK_STATS(alice, "100.0000 PROXY", "800.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_param_test2, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.ram.starting_block_for_distribution = 80;
  tgs.ram.ending_block_for_distribution = 81;
  tgs.ram.distribution_payment_block_interval_for_distribution = 800;

  tgs.beos.starting_block_for_distribution = 800;
  tgs.beos.ending_block_for_distribution = 810;
  tgs.beos.distribution_payment_block_interval_for_distribution = 800;

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  issue( N(alice), asset::from_string("100.0000 PROXY") );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 80 - control->head_block_num() - 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 79u );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 80u );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "5000000");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( liquid_ram_test, eosio_init_tester ) try {

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

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

  tgs.beos.starting_block_for_distribution = 60;
  tgs.beos.ending_block_for_distribution = 61;
  tgs.ram.starting_block_for_distribution = 80;
  tgs.ram.ending_block_for_distribution = 81;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  create_account_with_resources( config::gateway_account_name, N(xxxxxxxmario) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(xxxxxxxmario), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxxmario", 5600 ) );

  produce_blocks( 81 - control->head_block_num() );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxxmario", 5600 ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 82 );
  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "800.0000 BEOS", "5000000");

  BOOST_REQUIRE_EQUAL( success(), sellram( "xxxxxxxmario", 5600 ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( false_tests, eosio_init_tester ) try {

  test_global_state tgs;

  produce_blocks( 30 - control->head_block_num() );

  auto buffer = tgs.starting_block_for_initial_witness_election;
  tgs.starting_block_for_initial_witness_election = 0;
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("STARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION > 0"), change_params( tgs ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 30u );
  tgs.starting_block_for_initial_witness_election = buffer;

  checker( tgs, tgs.beos );
  checker( tgs, tgs.ram );
  checker( tgs, tgs.trustee );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_vote_test, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.distribution_payment_block_interval_for_distribution = 5;
  tgs.beos.starting_block_for_distribution = 55;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  create_account_with_resources( config::gateway_account_name, N(xxxxxxxmario) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(xxxxxxxmario), asset::from_string("5.0000 PROXY") ) );

  produce_blocks( 60 - control->head_block_num() );

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "800.0000 BEOS", "0");
  CHECK_STATS(bob, "5.0000 PROXY", "800.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( 8730859820578.5469, get_producer_info( N(bob) )["total_votes"].as_double() );

  produce_blocks( 100 - control->head_block_num() );

  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "4000.0000 BEOS", "0");
  CHECK_STATS(bob, "5.0000 PROXY", "4000.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( 43654299102892.734, get_producer_info( N(bob) )["total_votes"].as_double() );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  BOOST_REQUIRE_EQUAL( 43654299102892.734, get_producer_info( N(bob) )["total_votes"].as_double() );

  produce_blocks( 1 );

  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "4000.0000 BEOS", "0");
  CHECK_STATS(bob, "5.0000 PROXY", "4000.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( 43654299102892.734, get_producer_info( N(bob) )["total_votes"].as_double() );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  BOOST_REQUIRE_EQUAL( 43654299102892.734, get_producer_info( N(bob) )["total_votes"].as_double() );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_vote_test2, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block_for_distribution = 50;
  tgs.beos.distribution_payment_block_interval_for_distribution = 5;
  tgs.beos.starting_block_for_distribution = 55;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  create_account_with_resources( config::gateway_account_name, N(xxxxxxxmario) );
  create_account_with_resources( config::gateway_account_name, N(xxxxxxmario2) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(xxxxxxxmario), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(xxxxxxmario2), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("5.0000 PROXY") ) );

  produce_blocks( 60 - control->head_block_num() );

  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "400.0000 BEOS", "0");
  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "400.0000 BEOS", "0");
  CHECK_STATS(bob, "5.0000 PROXY", "400.0000 BEOS", "0");
  CHECK_STATS(carol, "5.0000 PROXY", "400.0000 BEOS", "0");

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );
  BOOST_REQUIRE_EQUAL( success(), create_producer( N(carol) ) );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( 0, get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( 13096289730867.82, get_producer_info( N(carol) )["total_votes"].as_double() );

  produce_blocks( 100 - control->head_block_num() - 2 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 98u );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( 21827149551446.367, get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( 21827149551446.375, get_producer_info( N(carol) )["total_votes"].as_double() );

  produce_blocks( 1 );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 102u );

  BOOST_REQUIRE_EQUAL( 21827149551446.367, get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( 21827149551446.375, get_producer_info( N(carol) )["total_votes"].as_double() );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 103u );

  BOOST_REQUIRE_EQUAL( 21827149551446.367, get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( 21827149551446.375, get_producer_info( N(carol) )["total_votes"].as_double() );

  produce_blocks( 110 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 110u );

  BOOST_REQUIRE_EQUAL( 26192579461735.641, get_producer_info( N(bob) )["total_votes"].as_double() );
  BOOST_REQUIRE_EQUAL( 26192579461735.648, get_producer_info( N(carol) )["total_votes"].as_double() );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( undelegate_block_test, eosio_init_tester ) try {
  //see issue #15

  test_global_state tgs;

  tgs.beos.starting_block_for_distribution = 100;
  tgs.beos.ending_block_for_distribution = 105;
  tgs.beos.distribution_payment_block_interval_for_distribution = 8;

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("cannot unstake during distribution period"), unstake( N(beos.distrib), N(alice), asset::from_string("10.0000 BEOS"), asset::from_string("10.0000 BEOS") ) );

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
  tgs.beos.amount_of_reward = asset::from_string("51000000.0000 BEOS").get_amount();

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  produce_blocks( 235 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 235u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("no balance object found"), stake( N(alice), N(bob), _10, _10, true/*transfer*/ ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("000.0010 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("000.0001 PROXY") ) );

  produce_blocks( 242 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 242u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("no balance object found"), stake( N(alice), N(bob), _10, _10, true/*transfer*/ ) );

  produce_blocks( 248 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("no balance object found"), stake( N(alice), N(bob), _10, _10, true/*transfer*/ ) );

  produce_blocks( 270 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );
  CHECK_STATS(alice, "0.0010 PROXY", "185454545.4544 BEOS", "13636365");
  CHECK_STATS(bob, "0.0001 PROXY", "18545454.5456 BEOS", "1363635");

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("no balance object found"), stake( N(alice), N(bob), _10, _10, true/*transfer*/ ) );

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(alice), { N(bob) } ) );

  BOOST_REQUIRE_EQUAL( success(), unstake( N(alice), N(alice), _5, _5 ) );

  produce_block( fc::hours(3*24) );
  produce_blocks(1);

  asset balance = get_balance( N(alice) );
  BOOST_REQUIRE_EQUAL( _10, balance );  

  BOOST_REQUIRE_EQUAL( success(), stake( N(alice), N(bob), _5, _5, true/*transfer*/ ) );

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

  tgs.ram.starting_block_for_distribution = 200;
  tgs.ram.distribution_payment_block_interval_for_distribution = 10;
  tgs.ram.ending_block_for_distribution = 205;
  tgs.ram.amount_of_reward = 2222'0000;

  tgs.beos.starting_block_for_distribution = 200;
  tgs.beos.distribution_payment_block_interval_for_distribution = 2;
  tgs.beos.ending_block_for_distribution = 206;
  tgs.beos.amount_of_reward = asset::from_string("50000000.0000 BEOS").get_amount();

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("1.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("1.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( "user must stake before they can vote" ), vote_producer( N(alice), { N(dan) } ) );

  produce_blocks( 206 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 206u );
  CHECK_STATS(alice, "1.0000 PROXY", "50000000.0000 BEOS", "5555000");
  CHECK_STATS(bob, "1.0000 PROXY", "50000000.0000 BEOS", "5555000");
  CHECK_STATS(carol, "1.0000 PROXY", "50000000.0000 BEOS", "5555000");
  CHECK_STATS(dan, "1.0000 PROXY", "50000000.0000 BEOS", "5555000");

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

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_no_balance ), stake( N(dan), N(bob), asset::from_string("11.0000 BEOS"), _0, false/*transfer*/ ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_no_balance ), stake( N(dan), N(bob), asset::from_string("11.0000 BEOS"), _0, true/*transfer*/ ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_overdrawn_balance ), stake( N(alice), N(bob), asset::from_string("11.0000 BEOS"), _0, false/*transfer*/ ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_overdrawn_balance ), stake( N(alice), N(bob), asset::from_string("11.0000 BEOS"), _0, true/*transfer*/ ) );

  BOOST_REQUIRE_EQUAL( success(), stake( N(alice), N(carol), asset::from_string("1.0000 BEOS"), _0, false/*transfer*/ ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( delegate_block_test3, eosio_init_tester ) try {

  asset _0 = asset::from_string("0.0000 BEOS");
  asset _5 = asset::from_string("5.0000 BEOS");
  asset _10 = asset::from_string("10.0000 BEOS");
  asset _20 = asset::from_string("20.0000 BEOS");

  asset _reward_quarter = asset::from_string("37500000.0000 BEOS");
  asset _reward_half = asset::from_string("75000000.0000 BEOS");
  asset _reward = asset::from_string("150000000.0000 BEOS");

  test_global_state tgs;

  tgs.starting_block_for_initial_witness_election = 1;

  tgs.ram.starting_block_for_distribution = 200;
  tgs.ram.distribution_payment_block_interval_for_distribution = 10;
  tgs.ram.ending_block_for_distribution = 205;
  tgs.ram.amount_of_reward = 500'0000;

  tgs.beos.starting_block_for_distribution = 200;
  tgs.beos.distribution_payment_block_interval_for_distribution = 10;
  tgs.beos.ending_block_for_distribution = 206;
  tgs.beos.amount_of_reward = _reward.get_amount();

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

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

  BOOST_REQUIRE_EQUAL( success(), stake( N(bob), N(alice), _10, _10, false/*transfer*/ ) );
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

  tgs.ram.starting_block_for_distribution = 200;
  tgs.ram.distribution_payment_block_interval_for_distribution = 10;
  tgs.ram.ending_block_for_distribution = 205;
  tgs.ram.amount_of_reward = 2222'0000;

  tgs.beos.starting_block_for_distribution = 200;
  tgs.beos.distribution_payment_block_interval_for_distribution = 2;
  tgs.beos.ending_block_for_distribution = 206;
  tgs.beos.amount_of_reward = asset::from_string("50000000.0000 BEOS").get_amount();

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

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

  CHECK_STATS( alice, "1.0000 PROXY", "100000000.0000 BEOS", "11110000");
  CHECK_STATS( bob, "1.0000 PROXY", "100000000.0000 BEOS", "11110000");

  BOOST_REQUIRE_EQUAL( _0, get_balance( N(eosio.saving) ) );
  BOOST_REQUIRE_EQUAL( _0, get_balance( N(eosio.bpay) ) );
  BOOST_REQUIRE_EQUAL( _0, get_balance( N(eosio.vpay) ) );

  asset supply01 = get_token_supply();

  BOOST_REQUIRE_EQUAL( success(), claimrewards( N(alice) ) );
  produce_blocks(1);
  BOOST_REQUIRE_EQUAL( asset::from_string("124.1097 BEOS"), get_balance( N(eosio.saving) ) );
  BOOST_REQUIRE_EQUAL( asset::from_string("3.8194 BEOS"), get_balance( N(eosio.bpay) ) );
  BOOST_REQUIRE_EQUAL( asset::from_string("23.2706 BEOS"), get_balance( N(eosio.vpay) ) );
  CHECK_STATS( alice, "1.0000 PROXY", "100000003.9374 BEOS", "11110000");

  asset supply02 = get_token_supply();
  asset sum = supply01 + get_balance( N(eosio.saving) ) + get_balance( N(eosio.bpay) ) + get_balance( N(eosio.vpay) );
  sum+= asset::from_string("3.9374 BEOS");
  BOOST_REQUIRE_EQUAL( supply02, sum );

  BOOST_REQUIRE_EQUAL( success(), claimrewards( N(bob) ) );
  produce_blocks(1);
  BOOST_REQUIRE_EQUAL( asset::from_string("125.3508 BEOS"), get_balance( N(eosio.saving) ) );
  BOOST_REQUIRE_EQUAL( asset::from_string("0.0000 BEOS"), get_balance( N(eosio.bpay) ) );
  BOOST_REQUIRE_EQUAL( asset::from_string("23.5033 BEOS"), get_balance( N(eosio.vpay) ) );
  CHECK_STATS( bob, "1.0000 PROXY", "100000003.8969 BEOS", "11110000");

  asset supply03 = get_token_supply();
  sum = supply01 + get_balance( N(eosio.saving) ) + get_balance( N(eosio.bpay) ) + get_balance( N(eosio.vpay) );
  sum+= asset::from_string("3.9374 BEOS");
  sum+= asset::from_string("3.8969 BEOS");
  BOOST_REQUIRE_EQUAL( supply03, sum );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg( message_once_per_day ), claimrewards( N(alice) ) );

  produce_block( fc::hours(24) );
  produce_blocks(1);

  BOOST_REQUIRE_EQUAL( success(), claimrewards( N(bob) ) );
  CHECK_STATS( bob, "1.0000 PROXY", "100016770.7497 BEOS", "11110000");

  BOOST_REQUIRE_EQUAL( success(), claimrewards( N(alice) ) );
  CHECK_STATS( alice, "1.0000 PROXY", "100005036.8236 BEOS", "11110000");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( trustee_reward_test, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block_for_distribution = 100;
  tgs.beos.ending_block_for_distribution = 110;
  tgs.beos.distribution_payment_block_interval_for_distribution = 8;
  tgs.beos.amount_of_reward = 200000;
  tgs.trustee.amount_of_reward = 100000;

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", "0.0000 BEOS", "");

  produce_blocks( 100 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", "10.0000 BEOS", "");

  issue( N(beos.trustee), asset::from_string("10.0000 PROXY") );

  produce_blocks( 110 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 110u );

  CHECK_STATS(beos.trustee, "10.0000 PROXY", "40.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( distrib_onblock_call_test, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block_for_distribution = 100;
  tgs.beos.ending_block_for_distribution = 200;
  tgs.beos.distribution_payment_block_interval_for_distribution = 1;
  tgs.beos.amount_of_reward = 200'000;

  tgs.ram.starting_block_for_distribution = 1100;
  tgs.ram.ending_block_for_distribution = 1200;
  tgs.ram.distribution_payment_block_interval_for_distribution = 1;
  tgs.ram.amount_of_reward = 200'000;

  tgs.trustee.amount_of_reward = 100'000;

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

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

  tgs.beos.starting_block_for_distribution = 180;
  tgs.beos.ending_block_for_distribution = tgs.beos.starting_block_for_distribution + reward_period - 1;
  tgs.beos.distribution_payment_block_interval_for_distribution = 1;
  tgs.beos.amount_of_reward = 10000;

  tgs.ram.starting_block_for_distribution = 280;
  tgs.ram.ending_block_for_distribution = tgs.ram.starting_block_for_distribution + reward_period - 1;
  tgs.ram.distribution_payment_block_interval_for_distribution = 1;
  tgs.ram.amount_of_reward = 1000;

  tgs.trustee.amount_of_reward = 10000;

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  create_accounts_with_resources( config::system_account_name, no_of_accounts );

  BOOST_CHECK( control->head_block_num() < tgs.beos.starting_block_for_distribution );

  produce_blocks( tgs.beos.ending_block_for_distribution - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.beos.ending_block_for_distribution );

  produce_blocks( tgs.ram.ending_block_for_distribution - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.ram.ending_block_for_distribution );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", ASSET_STRING(reward_period * tgs.trustee.amount_of_reward, BEOS), "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( many_accounts_test2, eosio_init_bigstate_tester ) try {
  /*
      Reward periods for stake and ram are the same. No proxies for accounts.
  */

  reward_period = 20;

  tgs.beos.starting_block_for_distribution = 180;
  tgs.beos.ending_block_for_distribution = tgs.beos.starting_block_for_distribution + reward_period - 1;
  tgs.beos.distribution_payment_block_interval_for_distribution = 1;
  tgs.beos.amount_of_reward = 10000;

  tgs.ram.starting_block_for_distribution = tgs.beos.starting_block_for_distribution;
  tgs.ram.ending_block_for_distribution = tgs.beos.ending_block_for_distribution;
  tgs.ram.distribution_payment_block_interval_for_distribution = tgs.beos.distribution_payment_block_interval_for_distribution;
  tgs.ram.amount_of_reward = 1000;

  tgs.trustee.amount_of_reward = 10000;

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  create_accounts_with_resources( config::system_account_name, no_of_accounts );

  BOOST_CHECK( control->head_block_num() < tgs.beos.starting_block_for_distribution );

  produce_blocks( tgs.beos.ending_block_for_distribution - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.beos.ending_block_for_distribution );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", ASSET_STRING(reward_period * tgs.trustee.amount_of_reward, BEOS), "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( many_accounts_test3, eosio_init_bigstate_tester ) try {
  /*
      Reward periods for stake and ram are different. Proxies for accounts.
  */

  reward_period = 20;

  tgs.beos.starting_block_for_distribution = 180 + no_of_accounts;
  tgs.beos.ending_block_for_distribution = tgs.beos.starting_block_for_distribution + reward_period - 1;
  tgs.beos.distribution_payment_block_interval_for_distribution = 1;
  tgs.beos.amount_of_reward = 10000 * no_of_accounts;

  tgs.ram.starting_block_for_distribution = 280 + no_of_accounts;
  tgs.ram.ending_block_for_distribution = tgs.ram.starting_block_for_distribution + reward_period - 1;
  tgs.ram.distribution_payment_block_interval_for_distribution = 1;
  tgs.ram.amount_of_reward = 1000 * no_of_accounts;

  tgs.trustee.amount_of_reward = 10000;

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  const uint64_t stake_reward_per_account = reward_period * tgs.beos.amount_of_reward / no_of_accounts;
  const uint64_t ram_reward_per_account = reward_period * tgs.ram.amount_of_reward / no_of_accounts;

  account_names_t accounts( create_accounts_with_resources( config::system_account_name, no_of_accounts ) );

  issue_for_accounts( accounts, asset::from_string("1.0000 PROXY") );

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", "0.0000 BEOS", "");

  BOOST_CHECK( control->head_block_num() < tgs.beos.starting_block_for_distribution );

  produce_blocks( tgs.beos.ending_block_for_distribution - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.beos.ending_block_for_distribution );

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", ASSET_STRING(stake_reward_per_account, BEOS), "");

  produce_blocks( tgs.ram.ending_block_for_distribution - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.ram.ending_block_for_distribution );

  CHECK_STATS(beos.trustee, "0.0000 PROXY", ASSET_STRING(reward_period * tgs.trustee.amount_of_reward, BEOS), "");

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", ASSET_STRING(stake_reward_per_account, BEOS), std::to_string(ram_reward_per_account).c_str());

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( many_accounts_test4, eosio_init_bigstate_tester ) try {
  /*
      Reward periods for stake and ram are the same. Proxies for accounts.
  */

  reward_period = 20;

  tgs.beos.starting_block_for_distribution = 180 + no_of_accounts;
  tgs.beos.ending_block_for_distribution = tgs.beos.starting_block_for_distribution + reward_period - 1;
  tgs.beos.distribution_payment_block_interval_for_distribution = 1;
  tgs.beos.amount_of_reward = 10000 * no_of_accounts;

  tgs.ram.starting_block_for_distribution = tgs.beos.starting_block_for_distribution;
  tgs.ram.ending_block_for_distribution = tgs.beos.ending_block_for_distribution;
  tgs.ram.distribution_payment_block_interval_for_distribution = 1;
  tgs.ram.amount_of_reward = 1000 * no_of_accounts;

  tgs.trustee.amount_of_reward = 10000;

  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  const uint64_t stake_reward_per_account = reward_period * tgs.beos.amount_of_reward / no_of_accounts;
  const uint64_t ram_reward_per_account = reward_period * tgs.ram.amount_of_reward / no_of_accounts;

  account_names_t accounts( create_accounts_with_resources( config::system_account_name, no_of_accounts ) );

  issue_for_accounts( accounts, asset::from_string("1.0000 PROXY") );

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", "0.0000 BEOS", "");

  BOOST_CHECK( control->head_block_num() < tgs.beos.starting_block_for_distribution );

  produce_blocks( tgs.beos.ending_block_for_distribution - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), tgs.beos.ending_block_for_distribution );

  for (auto& account : accounts)
    CHECK_STATS_(account, "1.0000 PROXY", ASSET_STRING(stake_reward_per_account, BEOS), std::to_string(ram_reward_per_account).c_str());

  CHECK_STATS(beos.trustee, "0.0000 PROXY", ASSET_STRING(reward_period * tgs.trustee.amount_of_reward, BEOS), "");

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(eosio_interchain_tests)

BOOST_FIXTURE_TEST_CASE( basic_lock_test, eosio_interchain_tester ) try {

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("5.0000 PROXY") ) );

  CHECK_STATS(bob, "5.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 240 - control->head_block_num() - 1 );

  CHECK_STATS(bob, "5.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );

  CHECK_STATS(bob, "5.0000 PROXY", "800.0000 BEOS", "5000000");

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 244u );

  CHECK_STATS(bob, "5.0000 PROXY", "800.0000 BEOS", "10000000");

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  CHECK_STATS(bob, "5.0000 PROXY", "800.0000 BEOS", "15000000");

  produce_blocks( 2 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(bob, "5.0000 PROXY", "1600.0000 BEOS", "15000000");

  produce_blocks( 10 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(bob, "5.0000 PROXY", "2400.0000 BEOS", "15000000");

  produce_blocks( 10 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(bob, "5.0000 PROXY", "3200.0000 BEOS", "15000000");
} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test2, eosio_interchain_tester ) try {

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  issue( N(alice), asset::from_string("100.0000 PROXY") );

  CHECK_STATS(alice, "100.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 240 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );

  CHECK_STATS(alice, "100.0000 PROXY", "800.0000 BEOS", "5000000");

  issue( N(bob), asset::from_string("50.0000 PROXY") );

  CHECK_STATS(bob, "50.0000 PROXY", "0.0000 BEOS", "0");

  produce_blocks( 3 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 244u );

  CHECK_STATS(alice, "", "", "8333333");
  CHECK_STATS(bob,   "", "", "1666667");

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  CHECK_STATS(alice, "", "", "11666666");
  CHECK_STATS(bob,   "", "", "3333334");

  produce_blocks( 2 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "100.0000 PROXY", "1333.3333 BEOS", "11666666");
  CHECK_STATS(bob,   "50.0000 PROXY", "266.6667 BEOS", "3333334");

  produce_blocks( 10 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "100.0000 PROXY" , "1866.6666 BEOS", "11666666");

  CHECK_STATS(bob, "50.0000 PROXY" , "533.3334 BEOS", "3333334");

  produce_blocks( 10 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "100.0000 PROXY" , "2399.9999 BEOS", "11666666");
  CHECK_STATS(bob,   "50.0000 PROXY" , "800.0001 BEOS", "3333334");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test3, eosio_interchain_tester ) try {

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("100.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );

  CHECK_STATS(alice, "100.0000 PROXY" , "800.0000 BEOS", "5000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("100.0000 PROXY") ) );

  CHECK_STATS(bob, "100.0000 PROXY" , "0.0000 BEOS", "0");

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "100.0000 PROXY" , "1200.0000 BEOS", "");

  CHECK_STATS(bob, "100.0000 PROXY" , "400.0000 BEOS", "");

  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("111.0000 PROXY") ) );
  CHECK_STATS(carol, "111.0000 PROXY" , "0.0000 BEOS", "0");

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS( alice, "" , "1457.2347 BEOS", "");
  CHECK_STATS( bob, "" , "657.2347 BEOS", "");
  CHECK_STATS( carol, "" , "285.5305 BEOS", "");

  issue( N(dan), asset::from_string("1500.9876 PROXY") );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS( alice, "" , "1501.3851 BEOS", "");//0,055188016('100/1811.9876') * 800 + 1457.2347 = 1501,3851128
  CHECK_STATS( bob, "" , "701.3851 BEOS", "");//0,055188016('100/1811.9876') * 800 + 657.2347 = 701,3851128
  CHECK_STATS( carol, "" , "334.5375 BEOS", "");//0,061258697('111/1811.9876') * 800 + 285.5305 = 334,5374576
  CHECK_STATS( dan, "" , "662.6922 BEOS", "");//0,828365271('1500.9876/1811.9876') * 800 = 662,6922168

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test4, eosio_interchain_tester ) try {

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  produce_blocks( 270 - control->head_block_num() - 3 );

  /*
    Block number 270 has 2 actions:
    a) issue for 'carol' account
    b) transfers staked BEOS-es to BEOS-es
  */
  issue( N(alice), asset::from_string("132.0000 PROXY") );
  issue( N(bob), asset::from_string("132.0000 PROXY") );
  issue( N(carol), asset::from_string("66.0000 PROXY") );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "", "320.0000 BEOS", "");
  CHECK_STATS(bob,   "", "320.0000 BEOS", "");
  CHECK_STATS(carol, "", "160.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test5, eosio_interchain_tester ) try {

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_TEST_MESSAGE( "Lack any locks" );
  produce_blocks( 270 - control->head_block_num() );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_lock_test6, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "Every issue is too late, is triggered after distribution period" );

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

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
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  issue( N(alice), asset::from_string("0.0002 PROXY") );
  issue( N(bob), asset::from_string("0.0002 PROXY") );
  issue( N(carol), asset::from_string("0.0001 PROXY") );

  issue( N(alice), asset::from_string("0.0002 PROXY") );
  issue( N(bob), asset::from_string("0.0002 PROXY") );
  issue( N(carol), asset::from_string("0.0001 PROXY") );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "", "320.0000 BEOS", "");
  CHECK_STATS(bob,   "", "320.0000 BEOS", "");
  CHECK_STATS(carol, "", "160.0000 BEOS", "");

  issue( N(alice), asset::from_string("0.0012 PROXY") );
  issue( N(bob), asset::from_string("0.0012 PROXY") );
  issue( N(carol), asset::from_string("0.0006 PROXY") );

  issue( N(alice), asset::from_string("0.0012 PROXY") );
  issue( N(bob), asset::from_string("0.0012 PROXY") );
  issue( N(carol), asset::from_string("0.0006 PROXY") );

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "", "640.0000 BEOS", "");
  CHECK_STATS(bob, "", "640.0000 BEOS", "");
  CHECK_STATS(carol, "", "320.0000 BEOS", "");

  issue( N(alice), asset::from_string("0.0022 PROXY") );
  issue( N(bob), asset::from_string("0.0022 PROXY") );
  issue( N(carol), asset::from_string("0.0011 PROXY") );

  issue( N(alice), asset::from_string("0.0022 PROXY") );
  issue( N(bob), asset::from_string("0.0022 PROXY") );
  issue( N(carol), asset::from_string("0.0011 PROXY") );

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "", "960.0000 BEOS", "");
  CHECK_STATS(bob, "", "960.0000 BEOS", "");
  CHECK_STATS(carol, "", "480.0000 BEOS", "");

  issue( N(alice), asset::from_string("0.0024 PROXY") );
  issue( N(bob), asset::from_string("0.0024 PROXY") );
  issue( N(carol), asset::from_string("0.0012 PROXY") );

  issue( N(alice), asset::from_string("0.0024 PROXY") );
  issue( N(bob), asset::from_string("0.0024 PROXY") );
  issue( N(carol), asset::from_string("0.0012 PROXY") );

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "", "1280.0000 BEOS", "");
  CHECK_STATS(bob, "", "1280.0000 BEOS", "");
  CHECK_STATS(carol, "", "640.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( manipulation_lock_test, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "2 accounts are alternately locked and decreased" );

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  issue( N(alice), asset::from_string("1.0000 PROXY") );

  CHECK_STATS(alice, "1.0000 PROXY", "0.0000 BEOS", "");

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "", "800.0000 BEOS", "");

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("overdrawn balance during withdraw"), withdraw( N(alice), asset::from_string("1.0001 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "", "800.0000 BEOS", "");

  issue( N(bob), asset::from_string("600.0000 PROXY") );

  CHECK_STATS(bob, "600.0000 PROXY", "0.0000 BEOS", "");

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "", "800.0000 BEOS", "");
  CHECK_STATS(bob, "", "800.0000 BEOS", "");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("600.0000 PROXY") ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "", "800.0000 BEOS", "");
  CHECK_STATS(bob, "", "800.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( manipulation_lock_test2, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "1 account - actions: issue, withdraw in different configurations" );

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "1.0000 PROXY", "800.0000 BEOS", "");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );

  CHECK_STATS(alice, "2.0000 PROXY", "800.0000 BEOS", "");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("2.0000 PROXY") ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "0.0000 PROXY", "800.0000 BEOS", "");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("3.0000 PROXY") ) );

  CHECK_STATS(alice, "3.0000 PROXY", "800.0000 BEOS", "");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("3.0000 PROXY") ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("33.0000 PROXY") ) );

  CHECK_STATS(alice, "33.0000 PROXY", "800.0000 BEOS", "");

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "33.0000 PROXY", "1600.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( manipulation_lock_test3, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "4 accounts - actions: issue, withdraw in different configurations" );

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("8.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("8.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "8.0000 PROXY", "200.0000 BEOS", "");
  CHECK_STATS(bob,   "8.0000 PROXY", "200.0000 BEOS", "");
  CHECK_STATS(carol, "8.0000 PROXY", "200.0000 BEOS", "");
  CHECK_STATS(dan,   "8.0000 PROXY", "200.0000 BEOS", "");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("16.0000 PROXY") ) );

  CHECK_STATS(alice, "24.0000 PROXY", "200.0000 BEOS", "");
  CHECK_STATS(bob,   "24.0000 PROXY", "200.0000 BEOS", "");
  CHECK_STATS(carol, "24.0000 PROXY", "200.0000 BEOS", "");
  CHECK_STATS(dan,   "0.0000 PROXY", "200.0000 BEOS", "");

  produce_blocks( 6 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("16.0000 PROXY") ) );

  CHECK_STATS(alice, "8.0000 PROXY", "466.6667 BEOS", "");
  CHECK_STATS(bob,   "8.0000 PROXY", "466.6667 BEOS", "");
  CHECK_STATS(carol, "24.0000 PROXY", "466.6667 BEOS", "");
  CHECK_STATS(dan,   "16.0000 PROXY", "200.0000 BEOS", "");

  produce_blocks( 7 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "8.0000 PROXY", "580.9524 BEOS", "");
  CHECK_STATS(bob,   "8.0000 PROXY", "580.9524 BEOS", "");
  CHECK_STATS(carol, "24.0000 PROXY", "809.5238 BEOS", "");
  CHECK_STATS(dan,   "16.0000 PROXY", "428.5714 BEOS", "");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("16.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("48.0000 PROXY") ) );

  produce_blocks( 7 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "0.0000 PROXY", "580.9524 BEOS", "");
  CHECK_STATS(bob,   "56.0000 PROXY", "1140.9524 BEOS", "");
  CHECK_STATS(carol, "24.0000 PROXY", "1049.5238 BEOS", "");
  CHECK_STATS(dan,   "0.0000 PROXY", "428.5714 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( performance_lock_test, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "1 account - a lot of locks" );

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  std::vector< action > v;

  for( int32_t i = 0; i < 1000; ++i )
    v.emplace_back( create_issue_action( N(alice), asset::from_string("0.0001 PROXY") ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "0.1000 PROXY", "800.0000 BEOS", "");

  v.clear();
  for( int32_t i = 0; i < 5000; ++i )
    v.emplace_back( create_issue_action( N(alice), asset::from_string("0.0001 PROXY") ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "0.6000 PROXY", "1600.0000 BEOS", "");

  v.clear();
  for( int32_t i = 0; i < 5000; ++i )
    v.emplace_back( create_issue_action( N(alice), asset::from_string("1000.0000 PROXY") ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "5000000.6000 PROXY", "2400.0000 BEOS", "");

  v.clear();
  for( int32_t i = 0; i < 1000; ++i )
    v.emplace_back( create_issue_action( N(alice), asset::from_string("10000.0000 PROXY") ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "15000000.6000 PROXY", "3200.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( performance_lock_test2, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "4 accounts - a lot of locks" );

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

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

  CHECK_STATS(alice, "0.1000 PROXY", "200.0000 BEOS", "");
  CHECK_STATS(bob,   "0.1000 PROXY", "200.0000 BEOS", "");
  CHECK_STATS(carol, "0.1000 PROXY", "200.0000 BEOS", "");
  CHECK_STATS(dan,   "0.1000 PROXY", "200.0000 BEOS", "");

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

  CHECK_STATS(alice, "2000.0000 PROXY", "520.0000 BEOS", "");
  CHECK_STATS(bob,   "2000.0000 PROXY", "520.0000 BEOS", "");
  CHECK_STATS(carol, "1000.0000 PROXY", "360.0000 BEOS", "");
  CHECK_STATS(dan,   "0.0000 PROXY", "200.0000 BEOS", "");

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

  CHECK_STATS(alice, "0.0000 PROXY", "520.0000 BEOS", "");
  CHECK_STATS(bob,   "0.0000 PROXY", "520.0000 BEOS", "");
  CHECK_STATS(carol, "6000.0000 PROXY", "796.3636 BEOS", "");
  CHECK_STATS(dan,   "5000.0000 PROXY", "563.6364 BEOS", "");

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

  //CHECK_STATS(alice, "17000.0000 PROXY", "920.0000 BEOS", "");
  CHECK_STATS(alice, "12000.0000 PROXY", "920.0000 BEOS", "");
  //CHECK_STATS(bob,   "17000.0000 PROXY", "920.0000 BEOS", "");
  CHECK_STATS(bob,   "12000.0000 PROXY", "920.0000 BEOS", "");
  CHECK_STATS(carol, "0.0000 PROXY", "796.3636 BEOS", "");
  CHECK_STATS(dan,   "0.0000 PROXY", "563.6364 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( false_tests, eosio_interchain_tester ) try {

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

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
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice,"1.0000 PROXY", "800.0000 BEOS", "5000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("1.0000 PROXY") ) );

  produce_blocks( 2 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 244u );

  CHECK_STATS(alice,"8.0000 PROXY", "800.0000 BEOS", "10000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 3 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  CHECK_STATS(alice,"0.0000 PROXY", "800.0000 BEOS", "10000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("0.6000 PROXY") ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice,"0.6000 PROXY", "1600.0000 BEOS", "10000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.2000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );

  produce_blocks( 7 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice,"0.2000 PROXY", "2400.0000 BEOS", "10000000");

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

  CHECK_STATS(alice,"0.0000 PROXY", "2400.0000 BEOS", "10000000");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( performance_decrease_test2, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "Decreasing balance for 4 accounts" );

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("2.0000 PROXY") ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("2.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice,"2.0000 PROXY", "400.0000 BEOS", "2500000");
  CHECK_STATS(bob,  "2.0000 PROXY", "400.0000 BEOS", "2500000");

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("overdrawn balance during withdraw"), withdraw( N(bob), asset::from_string("6.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("2.0000 PROXY") ) );

  produce_blocks( 3 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 244u );

  CHECK_STATS(alice,"2.0000 PROXY", "400.0000 BEOS", "7500000");
  CHECK_STATS(bob  ,"0.0000 PROXY", "400.0000 BEOS", "2500000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("10.0000 PROXY") ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  CHECK_STATS(alice, "0.0000 PROXY", "400.0000 BEOS", "7500000");
  CHECK_STATS(bob, "8.0000 PROXY", "400.0000 BEOS", "7500000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice,"0.0000 PROXY", "400.0000 BEOS", "7500000");
  CHECK_STATS(bob, "0.0000 PROXY", "400.0000 BEOS", "7500000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(carol), asset::from_string("48.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(dan), asset::from_string("48.0000 PROXY") ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "0.0000 PROXY", "400.0000 BEOS", "");
  CHECK_STATS(bob,   "0.0000 PROXY", "400.0000 BEOS", "");
  CHECK_STATS(carol, "48.0000 PROXY", "400.0000 BEOS", "");
  CHECK_STATS(dan,   "48.0000 PROXY", "400.0000 BEOS", "");

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

  CHECK_STATS(alice, "0.0000 PROXY", "400.0000 BEOS", "");
  CHECK_STATS(bob,   "48.0000 PROXY", "800.0000 BEOS", "");
  CHECK_STATS(carol, "48.0000 PROXY", "800.0000 BEOS", "");
  CHECK_STATS(dan,   "0.0000 PROXY", "400.0000 BEOS", "");
} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_1, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( " Test issue, withdraw for one account");

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "8.0000 PROXY", "800.0000 BEOS", "5000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("16.0000 PROXY") ) );
  
  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "0.0000 PROXY", "800.0000 BEOS", "5000000");

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("8.0000 PROXY") ) );
  
  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );
  
  CHECK_STATS(alice,  "8.0000 PROXY", "1600.0000 BEOS", "5000000");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("8.0000 PROXY") ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice,  "0.0000 PROXY", "1600.0000 BEOS", "5000000");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_2, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( " Test issue, withdraw for four accounts");

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  const auto& StN = eosio::chain::string_to_name;
  using Accounts = std::vector<std::string>;
  Accounts accounts = {"alice", "bob", "carol", "dan"};

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), issue( StN(_acc.c_str()), asset::from_string("8.0000 PROXY") ) );
  }

  produce_blocks( 240 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 240u );

  CHECK_STATS(alice, "8.0000 PROXY", "200.0000 BEOS", "1250000");
  CHECK_STATS(bob,   "8.0000 PROXY", "200.0000 BEOS", "1250000");
  CHECK_STATS(carol, "8.0000 PROXY", "200.0000 BEOS", "1250000");
  CHECK_STATS(dan,   "8.0000 PROXY", "200.0000 BEOS", "1250000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), issue( StN(_acc.c_str()), asset::from_string("8.0000 PROXY") ) );
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("16.0000 PROXY") ) );
  }

  produce_blocks(2);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "0.0000 PROXY", "200.0000 BEOS", "1250000");
  CHECK_STATS(bob,   "0.0000 PROXY", "200.0000 BEOS", "1250000");
  CHECK_STATS(carol, "0.0000 PROXY", "200.0000 BEOS", "3750000");
  CHECK_STATS(dan,   "0.0000 PROXY", "200.0000 BEOS", "3750000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), issue( StN(_acc.c_str()), asset::from_string("8.0000 PROXY") ) );
  }

  produce_blocks(6);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "8.0000 PROXY", "400.0000 BEOS", "1250000");
  CHECK_STATS(bob,   "8.0000 PROXY", "400.0000 BEOS", "1250000");
  CHECK_STATS(carol, "8.0000 PROXY", "400.0000 BEOS", "3750000");
  CHECK_STATS(dan,   "8.0000 PROXY", "400.0000 BEOS", "3750000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("8.0000 PROXY") ) );
  }

  produce_blocks(6);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_3, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( " Test issue, withdraw for n dynamic accounts");

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

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
  
  CHECK_STATS(bozydar,  "10.0000 PROXY", "160.0000 BEOS", "1000000");
  CHECK_STATS(bogumil,  "10.0000 PROXY", "160.0000 BEOS", "1000000");
  CHECK_STATS(perun,    "10.0000 PROXY", "160.0000 BEOS", "1000000");
  CHECK_STATS(swiatowid,"10.0000 PROXY", "160.0000 BEOS", "1000000");
  CHECK_STATS(weles,    "10.0000 PROXY", "160.0000 BEOS", "1000000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("10.0000 PROXY") ) );
  }

  produce_blocks(5);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(bozydar,  "0.0000 PROXY", "160.0000 BEOS", "1000000");
  CHECK_STATS(bogumil,  "0.0000 PROXY", "160.0000 BEOS", "1000000");
  CHECK_STATS(perun,    "0.0000 PROXY", "160.0000 BEOS", "1000000");
  CHECK_STATS(swiatowid,"0.0000 PROXY", "160.0000 BEOS", "1000000");
  CHECK_STATS(weles,    "0.0000 PROXY", "160.0000 BEOS", "6000000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), issue( StN(_acc.c_str()), asset::from_string("5.0000 PROXY") ) );
  }

  produce_blocks(5);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(bozydar,  "5.0000 PROXY", "320.0000 BEOS", "1000000");
  CHECK_STATS(bogumil,  "5.0000 PROXY", "320.0000 BEOS", "1000000");
  CHECK_STATS(perun,    "5.0000 PROXY", "320.0000 BEOS", "1000000");
  CHECK_STATS(swiatowid,"5.0000 PROXY", "320.0000 BEOS", "1000000");
  CHECK_STATS(weles,    "5.0000 PROXY", "320.0000 BEOS", "6000000");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("5.0000 PROXY") ) );
  }

  produce_blocks(5);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_4, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "Test issue, withdraw for created and dynamic accounts");

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

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

  CHECK_STATS(perun,    "20.0000 PROXY", "266.6667 BEOS", "1666667");
  CHECK_STATS(swiatowid,"20.0000 PROXY", "266.6667 BEOS", "1666667");
  CHECK_STATS(alice,    "10.0000 PROXY", "133.3333 BEOS", "833333");
  CHECK_STATS(dan,      "10.0000 PROXY", "133.3333 BEOS", "833333");

  for(const auto& _acc : accounts) {
    BOOST_REQUIRE_EQUAL( success(), withdraw( StN(_acc.c_str()), asset::from_string("10.0000 PROXY") ) );
  }

  produce_blocks(6);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(perun,    "10.0000 PROXY", "666.6667 BEOS", "6666667");
  CHECK_STATS(swiatowid,"10.0000 PROXY", "666.6667 BEOS", "6666667");
  CHECK_STATS(alice,    "0.0000 PROXY", "133.3333 BEOS", "833333");
  CHECK_STATS(dan,      "0.0000 PROXY", "133.3333 BEOS", "833333");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(perun), asset::from_string("10.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(swiatowid), asset::from_string("10.0000 PROXY") ) );

  produce_blocks(8);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice,    "0.0000 PROXY", "133.3333 BEOS", "833333");
  CHECK_STATS(dan,      "0.0000 PROXY", "133.3333 BEOS", "833333");

  produce_blocks(10);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice,    "0.0000 PROXY", "133.3333 BEOS", "833333");
  CHECK_STATS(dan,      "0.0000 PROXY", "133.3333 BEOS", "833333");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( creating_short_names, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "Creating names with length less than 12 chars - creator beos.gateway");

  create_account_with_resources( config::gateway_account_name, N(mario) );
  create_account_with_resources( config::gateway_account_name, N(mario.mar) );
  create_account_with_resources( config::gateway_account_name, N(12345123451) );
  create_account_with_resources( config::gateway_account_name, N(1234.x) );

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()
