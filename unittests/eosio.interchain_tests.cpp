#include <boost/test/unit_test.hpp>
#include <eosio/testing/tester.hpp>
#include <eosio/chain/abi_serializer.hpp>

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

static const uint64_t DEFAULT_RAM = 10000;

struct actions: public tester
{
  abi_serializer beos_init_abi_ser;
  abi_serializer beos_gateway_abi_ser;
  abi_serializer token_abi_ser;
  abi_serializer beos_distrib_abi_ser;
  abi_serializer system_abi_ser;

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
      ( "quantity", quantity ),
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

  action_result withdraw( account_name owner, asset quantity )
  {
    return push_action( owner, N(withdraw), mvo()
        ( "owner", owner )
        ( "quantity", quantity ),
        beos_gateway_abi_ser,
        N(beos.gateway)
      );
  }

  action_result withdrawall( account_name removed, asset symbol )
  {
    return push_action( removed, N(withdrawall), mvo()
        ( "removed", removed )
        ( "symbol", symbol ),
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
        ( "stake_net_quantity", stake_net_quantity )
        ( "stake_cpu_quantity", stake_cpu_quantity ),
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

  eosio_interchain_tester()
  {
    produce_blocks( 2 );

    create_accounts({
                      N(eosio.token), N(eosio.ram), N(eosio.ramfee), N(eosio.stake),
                      N(eosio.bpay), N(eosio.vpay), N(eosio.saving), N(eosio.names),
                      N(beos.init)
                    });

    prepare_account( N(eosio.token), eosio_token_wast, eosio_token_abi, &token_abi_ser );

    create_currency( N(eosio.token), config::distribution_account_name, asset::from_string("10000000000.0000 BEOS") );
    create_currency( N(eosio.token), config::gateway_account_name, asset::from_string("10000000000.0000 PROXY") );
    produce_blocks( 1 );

    prepare_account( config::system_account_name, eosio_system_wast, eosio_system_abi, &system_abi_ser );
    prepare_account( N(beos.init), eosio_init_wast, eosio_init_abi, &beos_init_abi_ser );
    prepare_account( config::gateway_account_name, eosio_gateway_wast, eosio_gateway_abi, &beos_gateway_abi_ser );
    prepare_account( config::distribution_account_name, eosio_distribution_wast, eosio_distribution_abi, &beos_distrib_abi_ser );

    BOOST_REQUIRE_EQUAL( success(), initresource( config::system_account_name,
                                                    100'000'000,
                                                    asset::from_string("1000.0000 BEOS"),
                                                    asset::from_string("1000.0000 BEOS")
                                                  )
                        );

    create_account_with_resources( config::system_account_name, N(alice) );
    create_account_with_resources( config::system_account_name, N(bob) );
    create_account_with_resources( config::system_account_name, N(carol) );
    create_account_with_resources( config::system_account_name, N(dan) );
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
    vector<char> data = get_row_by_account( config::system_account_name, acc, N(userres), acc );

    if( data.empty() )
    {
      return mvo()
        ( "balance", balance )
        ( "staked_balance", "0.0000 BEOS" )
        ( "staked_ram", "0.0000 BEOS" );
    }
    else
    {
      auto resources = system_abi_ser.binary_to_variant( "user_resources", data, abi_serializer_max_time );
      auto net_weight = resources["net_weight"].as<asset>();
      auto cpu_weight = resources["cpu_weight"].as<asset>();
      auto ram_bytes = resources["ram_bytes"].as<int64_t>();

      auto total_net_cpu = net_weight + cpu_weight;

      return mvo()
        ( "balance", balance )
        ( "staked_balance", total_net_cpu )
        ( "staked_ram", ram_bytes );
    }
  }

  transaction_trace_ptr create_account_with_resources( account_name creator, account_name a, int64_t bytes = DEFAULT_RAM ) {
    signed_transaction trx;
    set_transaction_headers(trx);

    authority owner_auth;

    owner_auth =  authority( get_public_key( a, "owner" ) );

    trx.actions.emplace_back( vector<permission_level>{{creator,config::active_name}},
                              newaccount{
                                  .creator  = creator,
                                  .name     = a,
                                  .owner    = owner_auth,
                                  .active   = authority( get_public_key( a, "active" ) )
                              });

    trx.actions.emplace_back( get_action( config::system_account_name, N(delegateram), vector<permission_level>{{creator,config::active_name}},
                                          mvo()
                                          ("payer", creator)
                                          ("receiver", a)
                                          ("bytes", bytes) )
                            );

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

};

class eosio_init_tester: public eosio_interchain_tester
{
  public:
 
  eosio_init_tester()
  {

  } 

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

  action_result stake( const account_name& sender, const asset& net, const asset& cpu )
  {
    return push_action( sender, N(delegatebw), mvo()
        ("from",     sender)
        ("receiver", sender)
        ("stake_net_quantity", net)
        ("stake_cpu_quantity", cpu)
        ("transfer", 0 ),
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

#define CHECK_STATS(_accName, _expectedBalance, _expectedStakedBalance, _expectedStakedRam)   \
{                                                                                             \
    std::string _expectedStakedRam2 = _expectedStakedRam;                                     \
    if( _expectedStakedRam2.size() )                                                          \
    {                                                                                         \
      auto val = std::stol( _expectedStakedRam2 );                                            \
      _expectedStakedRam2 = std::to_string( DEFAULT_RAM + val );                              \
    }                                                                                         \
    auto stats = check_data( N(_accName) );                                                   \
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

  BOOST_REQUIRE_EQUAL( success(), initresource( config::distribution_account_name,
                                                  100'000'000,
                                                  asset::from_string("1000.0000 BEOS"),
                                                  asset::from_string("1000.0000 BEOS")
                                                )
                      );

  create_account_with_resources( config::distribution_account_name, N(xxxxxxxmario) );
  create_account_with_resources( config::distribution_account_name, N(xxxxxxmario2) );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxxmario", 5600 ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxmario2", 15600 ) );

  produce_blocks( 248 - control->head_block_num() );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 248u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxxmario", 5601 ) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxmario2", 15601 ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 249u );

  //Important!!! What to do, when RAM market doesn't exist.
  //BOOST_REQUIRE_EQUAL( success(), sellram( "xxxxxxxmario", 5600 ) );
  //BOOST_REQUIRE_EQUAL( success(), sellram( "xxxxxxmario2", 15600 ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( liquid_ram_test2, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.ram.starting_block_for_distribution = 80;
  tgs.ram.ending_block_for_distribution = 81;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), initresource( config::distribution_account_name,
                                                  100'000'000,
                                                  asset::from_string("1000.0000 BEOS"),
                                                  asset::from_string("1000.0000 BEOS")
                                                )
                      );

  create_account_with_resources( config::distribution_account_name, N(xxxxxxxmario) );
  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxxmario", 5600 ) );

  produce_blocks( 81 - control->head_block_num() );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("RAM shouldn't be liquid during distribution period"), sellram( "xxxxxxxmario", 5600 ) );

  produce_blocks( 1 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 82 );

  //Important!!! What to do, when RAM market doesn't exist.
  //BOOST_REQUIRE_EQUAL( success(), sellram( "xxxxxxxmario", 5600 ) );

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

  tgs.beos.starting_block_for_distribution = 50;
  tgs.beos.distribution_payment_block_interval_for_distribution = 5;
  tgs.beos.starting_block_for_distribution = 55;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), initresource( config::distribution_account_name,
                                                  100'000'000,
                                                  asset::from_string("1000.0000 BEOS"),
                                                  asset::from_string("1000.0000 BEOS")
                                                )
                      );

  create_account_with_resources( config::distribution_account_name, N(xxxxxxxmario) );

  BOOST_REQUIRE_EQUAL( success(), issue( N(bob), asset::from_string("5.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), issue( N(xxxxxxxmario), asset::from_string("5.0000 PROXY") ) );

  produce_blocks( 60 - control->head_block_num() );

  BOOST_REQUIRE_EQUAL( success(), create_producer( N(bob) ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  CHECK_STATS(xxxxxxxmario, "5.0000 PROXY", "800.0000 BEOS", "0");
  CHECK_STATS(bob, "5.0000 PROXY", "800.0000 BEOS", "0");

  auto prod = get_producer_info( N(bob) );
  BOOST_REQUIRE_EQUAL( 0, prod["total_votes"].as_double() );

  produce_blocks( 100 - control->head_block_num() );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );
  prod = get_producer_info( N(bob) );
  BOOST_REQUIRE_EQUAL( 0, prod["total_votes"].as_double() );

  produce_blocks( 1 );

  //Important!!! Voting( 'delegatebw' action ) must work.
  // BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );
  // prod = get_producer_info( N(bob) );
  // BOOST_REQUIRE_EQUAL( 120049322532.95502, prod["total_votes"].as_double() );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_vote_test2, eosio_init_tester ) try {

  test_global_state tgs;

  tgs.beos.starting_block_for_distribution = 50;
  tgs.beos.distribution_payment_block_interval_for_distribution = 5;
  tgs.beos.starting_block_for_distribution = 55;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  BOOST_REQUIRE_EQUAL( success(), initresource( config::distribution_account_name,
                                                  100'000'000,
                                                  asset::from_string("1000.0000 BEOS"),
                                                  asset::from_string("1000.0000 BEOS")
                                                )
                      );

  create_account_with_resources( config::distribution_account_name, N(xxxxxxxmario) );
  create_account_with_resources( config::distribution_account_name, N(xxxxxxmario2) );

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

  auto prod = get_producer_info( N(bob) );
  BOOST_REQUIRE_EQUAL( 0, prod["total_votes"].as_double() );

  prod = get_producer_info( N(carol) );
  BOOST_REQUIRE_EQUAL( 0, prod["total_votes"].as_double() );

  produce_blocks( 100 - control->head_block_num() - 2 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 98u );

  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );
  BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  prod = get_producer_info( N(bob) );
  BOOST_REQUIRE_EQUAL( 0, prod["total_votes"].as_double() );

  prod = get_producer_info( N(carol) );
  BOOST_REQUIRE_EQUAL( 0, prod["total_votes"].as_double() );

  produce_blocks( 1 );

  //Important!!! Voting( 'delegatebw' action ) must work.
  //BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxxmario), { N(bob) } ) );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 101u );

  prod = get_producer_info( N(bob) );
  //BOOST_REQUIRE_EQUAL( 120049322532.95502, prod["total_votes"].as_double() );

  prod = get_producer_info( N(carol) );
  BOOST_REQUIRE_EQUAL( 0, prod["total_votes"].as_double() );

  //BOOST_REQUIRE_EQUAL( success(), vote_producer( N(xxxxxxmario2), { N(carol) } ) );

  BOOST_REQUIRE_EQUAL( control->head_block_num(), 101u );

  //prod = get_producer_info( N(bob) );
  //BOOST_REQUIRE_EQUAL( 120049322532.95502, prod["total_votes"].as_double() );

  //prod = get_producer_info( N(carol) );
  //BOOST_REQUIRE_EQUAL( 163703621635.84775, prod["total_votes"].as_double() );

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

  BOOST_TEST_MESSAGE( "1 account - actions: issue, withdraw, withdrawall in different configurations" );

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

  BOOST_REQUIRE_EQUAL( success(), withdrawall( N(alice), asset::from_string("0.0000 PROXY") ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  BOOST_REQUIRE_EQUAL( success(), issue( N(alice), asset::from_string("33.0000 PROXY") ) );

  CHECK_STATS(alice, "33.0000 PROXY", "800.0000 BEOS", "");

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "33.0000 PROXY", "1600.0000 BEOS", "");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( manipulation_lock_test3, eosio_interchain_tester ) try {

  BOOST_TEST_MESSAGE( "4 accounts - actions: issue, withdraw, withdrawall in different configurations" );

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

  BOOST_REQUIRE_EQUAL( success(), withdrawall( N(alice), asset::from_string("0.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdrawall( N(dan), asset::from_string("0.0000 PROXY") ) );
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
    v.emplace_back( std::move( create_issue_action( N(alice), asset::from_string("0.0001 PROXY") ) ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 240 - control->head_block_num() );

  CHECK_STATS(alice, "0.1000 PROXY", "800.0000 BEOS", "");

  v.clear();
  for( int32_t i = 0; i < 5000; ++i )
    v.emplace_back( std::move( create_issue_action( N(alice), asset::from_string("0.0001 PROXY") ) ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 250u );

  CHECK_STATS(alice, "0.6000 PROXY", "1600.0000 BEOS", "");

  v.clear();
  for( int32_t i = 0; i < 5000; ++i )
    v.emplace_back( std::move( create_issue_action( N(alice), asset::from_string("1000.0000 PROXY") ) ) );
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice, "5000000.6000 PROXY", "2400.0000 BEOS", "");

  v.clear();
  for( int32_t i = 0; i < 1000; ++i )
    v.emplace_back( std::move( create_issue_action( N(alice), asset::from_string("10000.0000 PROXY") ) ) );
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
    v.emplace_back( std::move( create_issue_action( N(alice), asset::from_string("0.0001 PROXY") ) ) );
    v.emplace_back( std::move( create_issue_action( N(bob),   asset::from_string("0.0001 PROXY") ) ) );
    v.emplace_back( std::move( create_issue_action( N(carol), asset::from_string("0.0001 PROXY") ) ) );
    v.emplace_back( std::move( create_issue_action( N(dan),   asset::from_string("0.0001 PROXY") ) ) );
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
      v.emplace_back( std::move( create_issue_action( N(alice), asset::from_string("1.9000 PROXY") ) ) );
      v.emplace_back( std::move( create_issue_action( N(carol), asset::from_string("0.9000 PROXY") ) ) );
      v.emplace_back( std::move( create_issue_action( N(bob),   asset::from_string("1.9000 PROXY") ) ) );
    }
    else
    {
      v.emplace_back( std::move( create_issue_action( N(alice), asset::from_string("2.0000 PROXY") ) ) );
      v.emplace_back( std::move( create_issue_action( N(carol), asset::from_string("1.0000 PROXY") ) ) );
      v.emplace_back( std::move( create_issue_action( N(bob),   asset::from_string("2.0000 PROXY") ) ) );
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
    v.emplace_back( std::move( create_issue_action( N(carol), asset::from_string("5.0000 PROXY") ) ) );

    if( i == 0 )
      v.emplace_back( std::move( create_issue_action( N(dan), asset::from_string("4.9000 PROXY") ) ) );
    else
      v.emplace_back( std::move( create_issue_action( N(dan), asset::from_string("5.0000 PROXY") ) ) );
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
  for( int32_t i = 0; i < 3000; ++i )
  {
    v.emplace_back( std::move( create_issue_action( N(alice), asset::from_string("5.0000 PROXY") ) ) );
    v.emplace_back( std::move( create_issue_action( N(bob), asset::from_string("5.0000 PROXY") ) ) );
  }
  locks( N(beos.gateway), std::move( v ) );

  produce_blocks( 8 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 273u );

  CHECK_STATS(alice, "17000.0000 PROXY", "920.0000 BEOS", "");
  CHECK_STATS(bob,   "17000.0000 PROXY", "920.0000 BEOS", "");
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

  BOOST_TEST_MESSAGE( "'withdrawall' action" );

  BOOST_REQUIRE_EQUAL( "action's authorizing actor 'fake.acc2' does not exist", withdrawall( N(fake.acc2), asset::from_string("5.5432 PROXY") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("unable to find key"), withdrawall( N(beos.gateway), asset::from_string("100.0000 ABC") ) );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 100u );

  BOOST_REQUIRE_EQUAL( wasm_assert_msg("symbol precision mismatch"), withdrawall( N(beos.gateway), asset::from_string("100.00 PROXY") ) );
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

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );
  CHECK_STATS(alice,"0.0000 PROXY", "", "");

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("0.1000 PROXY") ) );
  CHECK_STATS(alice,"0.0000 PROXY", "", "");

  produce_blocks( 6 );
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

  BOOST_REQUIRE_EQUAL( success(), withdraw( N(bob), asset::from_string("6.0000 PROXY") ) );

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
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(dan), asset::from_string("500.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdraw( N(alice), asset::from_string("500.0000 PROXY") ) );

  produce_blocks( 4 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice, "0.0000 PROXY", "400.0000 BEOS", "");
  CHECK_STATS(bob,   "48.0000 PROXY", "800.0000 BEOS", "");
  CHECK_STATS(carol, "48.0000 PROXY", "800.0000 BEOS", "");
  CHECK_STATS(dan,   "0.0000 PROXY", "400.0000 BEOS", "");
} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_1, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( " Test issue, withdraw and withdrawall for one account");

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

  BOOST_REQUIRE_EQUAL( success(), withdrawall( N(alice), asset::from_string("0.0000 PROXY") ) );

  produce_blocks( 9 );
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice,  "0.0000 PROXY", "1600.0000 BEOS", "5000000");

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_2, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( " Test issue, withdraw and withdrawall for four accounts");

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
    BOOST_REQUIRE_EQUAL( success(), withdrawall( StN(_acc.c_str()), asset::from_string("16.0000 PROXY") ) );
  }

  produce_blocks(6);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_3, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( " Test issue, withdraw and withdrawall for n dynamic accounts");

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  const auto& StN = eosio::chain::string_to_name;
  using Accounts = std::vector<std::string>;
  Accounts accounts = { "bozydar", "bogumil", "perun", "swiatowid", "weles"};

  for(const auto& _acc : accounts ) {
    create_account_with_resources( config::system_account_name, _acc.c_str() );
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
    BOOST_REQUIRE_EQUAL( success(), withdrawall( StN(_acc.c_str()), asset::from_string("8.0000 PROXY") ) );
  }

  produce_blocks(5);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( main_commands_test_4, eosio_interchain_tester ) try {
  BOOST_TEST_MESSAGE( "Test issue, withdraw and withdrawall for created and dynamic accounts");

  test_global_state tgs;
  BOOST_REQUIRE_EQUAL( success(), change_params( tgs ) );

  const auto& StN = eosio::chain::string_to_name;
  using Accounts = std::vector<std::string>;
  Accounts accounts = { "perun", "swiatowid" };

  for(const auto& _acc : accounts ) {
    create_account_with_resources( config::system_account_name, _acc.c_str() );
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

  //
  //BOOST_REQUIRE_EQUAL( success(), withdrawall( N(dan), asset::from_string("0.0000 PROXY") ) );
  //BOOST_REQUIRE_EQUAL( success(), withdrawall( N(alice), asset::from_string("0.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdrawall( N(perun), asset::from_string("10.0000 PROXY") ) );
  BOOST_REQUIRE_EQUAL( success(), withdrawall( N(swiatowid), asset::from_string("10.0000 PROXY") ) );

  produce_blocks(8);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 260u );

  CHECK_STATS(alice,    "0.0000 PROXY", "133.3333 BEOS", "833333");
  CHECK_STATS(dan,      "0.0000 PROXY", "133.3333 BEOS", "833333");

  produce_blocks(10);
  BOOST_REQUIRE_EQUAL( control->head_block_num(), 270u );

  CHECK_STATS(alice,    "0.0000 PROXY", "133.3333 BEOS", "833333");
  CHECK_STATS(dan,      "0.0000 PROXY", "133.3333 BEOS", "833333");

} FC_LOG_AND_RETHROW()
BOOST_AUTO_TEST_SUITE_END()
