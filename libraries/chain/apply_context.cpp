#include <algorithm>
#include <eosio/chain/apply_context.hpp>
#include <eosio/chain/controller.hpp>
#include <eosio/chain/transaction_context.hpp>
#include <eosio/chain/exceptions.hpp>
#include <eosio/chain/wasm_interface.hpp>
#include <eosio/chain/generated_transaction_object.hpp>
#include <eosio/chain/authorization_manager.hpp>
#include <eosio/chain/voting_manager.hpp>
#include <eosio/chain/resource_limits.hpp>
#include <eosio/chain/account_object.hpp>
#include <eosio/chain/global_property_object.hpp>
#include <eosio/chain/dbg_timer.hpp>
#include <boost/container/flat_set.hpp>
#include <boost/scope_exit.hpp>

//#define CAVEMEN_TIME_DEBUG

//#define CAVEMEN_DEBUG
#ifdef CAVEMEN_DEBUG
#define DBG(format, ... ) { FILE *pFile = fopen("debug.log","a"); fprintf(pFile,format "\n",__VA_ARGS__); fclose(pFile); }
#else
#define DBG(format, ... )
#endif

using boost::container::flat_set;

namespace eosio { namespace chain {

static inline void print_debug(account_name receiver, const action_trace& ar) {
   if (!ar.console.empty()) {
      auto prefix = fc::format_string(
                                      "\n[(${a},${n})->${r}]",
                                      fc::mutable_variant_object()
                                      ("a", ar.act.account)
                                      ("n", ar.act.name)
                                      ("r", receiver));
      dlog(prefix + ": CONSOLE OUTPUT BEGIN =====================\n"
           + ar.console
           + prefix + ": CONSOLE OUTPUT END   =====================" );
   }
}

inline void apply_context::change_any_resource_limits_impl( const account_name& acc, int64_t ram, int64_t net, int64_t cpu, bool is_distribution )const
{
   auto& resource_limit_mgr = control.get_mutable_resource_limits_manager();
   int64_t ram_bytes = 0;
   int64_t net_weight = 0;
   int64_t cpu_weight = 0;

   resource_limit_mgr.get_account_limits( acc, ram_bytes, net_weight, cpu_weight );
   ram_bytes += ram;
   net_weight += net;
   cpu_weight += cpu;

   if( is_distribution )
   {
    if (resource_limit_mgr.set_distribution_account_limits( acc, ram_bytes, net_weight, cpu_weight ))
        trx_context.validate_ram_usage.insert( acc );
   }
   else
   {
    if (resource_limit_mgr.set_account_limits( acc, ram_bytes, net_weight, cpu_weight ))
        trx_context.validate_ram_usage.insert( acc );
   }
}

inline void apply_context::change_distribution_resource_limits( const account_name& acc, int64_t ram, int64_t net, int64_t cpu )const {
  change_any_resource_limits_impl( acc, ram, net, cpu, true/*is_distribution*/ );
}

inline void apply_context::change_resource_limits( const account_name& acc, int64_t ram, int64_t net, int64_t cpu )const {
  change_any_resource_limits_impl( acc, ram, net, cpu, false/*is_distribution*/ );
}

void apply_context::exec_one( action_trace& trace )
{
   auto start = fc::time_point::now();

   action_receipt r;
   r.receiver         = receiver;
   r.act_digest       = digest_type::hash(act);

   trace.trx_id = trx_context.id;
   trace.block_num = control.pending_block_number();
   trace.block_time = control.pending_block_time();
   trace.producer_block_id = control.pending_producer_block_id();
   trace.act = act;
   trace.context_free = context_free;

   #ifdef CAVEMEN_TIME_DEBUG
      dbg_timer _dbg_timer( "apply_context::exec_one: receiver: %s, action.account: %s, action.name: %s", receiver.to_string().c_str(), act.account.to_string().c_str(), act.name.to_string().c_str() );
   #endif

   DBG("apply_context::exec_one: receiver: %s, action.account: %s, action.name: %s",
      receiver.to_string().c_str(), act.account.to_string().c_str(), act.name.to_string().c_str());
   DBG("apply_context::exec_one: first_authorizor: %s", trx_context.trx.first_authorizor().to_string().c_str());

   const auto& cfg = control.get_global_properties().configuration;
   try {
      try {
         const auto& a = control.get_account( receiver );
         privileged = a.privileged;
         auto native = control.find_apply_handler( receiver, act.account, act.name );
         if( native ) {
            if( trx_context.can_subjectively_fail && control.is_producing_block() ) {
               control.check_contract_list( receiver );
               control.check_action_list( act.account, act.name );
            }
            (*native)( *this );
         }

         if( a.code.size() > 0
             && !(act.account == config::system_account_name && act.name == N( setcode ) &&
                  receiver == config::system_account_name) ) {
            if( trx_context.can_subjectively_fail && control.is_producing_block() ) {
               control.check_contract_list( receiver );
               control.check_action_list( act.account, act.name );
            }
            try {
               control.get_wasm_interface().apply( a.code_version, a.code, *this );
            } catch( const wasm_exit& ) {}
         }
      } FC_RETHROW_EXCEPTIONS( warn, "pending console output: ${console}", ("console", _pending_console_output.str()) )
   } catch( fc::exception& e ) {

      #ifdef CAVEMEN_TIME_DEBUG
         _dbg_timer.write("apply_context::exec_one exception: receiver: %s, action.account: %s, action.name: %s, name: %s, what: %s",
                     receiver.to_string().c_str(), act.account.to_string().c_str(), act.name.to_string().c_str(), e.name(), e.what() );
         _dbg_timer.end();
      #endif

      DBG("apply_context::exec_one exception: receiver: %s, action.account: %s, action.name: %s, name: %s, what: %s",
         receiver.to_string().c_str(), act.account.to_string().c_str(), act.name.to_string().c_str(),
         e.name(), e.what() );
      trace.receipt = r; // fill with known data
      trace.except = e;
      finalize_trace( trace, start );
      throw;
   }

   r.global_sequence  = next_global_sequence();
   r.recv_sequence    = next_recv_sequence( receiver );

   const auto& account_sequence = db.get<account_sequence_object, by_name>(act.account);
   r.code_sequence    = account_sequence.code_sequence; // could be modified by action execution above
   r.abi_sequence     = account_sequence.abi_sequence;  // could be modified by action execution above

   for( const auto& auth : act.authorization ) {
      r.auth_sequence[auth.actor] = next_auth_sequence( auth.actor );
   }

   trace.receipt = r;

   trx_context.executed.emplace_back( move(r) );

   finalize_trace( trace, start );

   if ( control.contracts_console() ) {
      print_debug(receiver, trace);
   }

   #ifdef CAVEMEN_TIME_DEBUG
      _dbg_timer.end();
   #endif
}

void apply_context::finalize_trace( action_trace& trace, const fc::time_point& start )
{
   trace.account_ram_deltas = std::move( _account_ram_deltas );
   _account_ram_deltas.clear();

   trace.console = _pending_console_output.str();
   reset_console();

   trace.elapsed = fc::time_point::now() - start;
}

void apply_context::reward_stake( const account_name& account, int64_t val)
{
   int64_t stake_net = val / 2;
   int64_t stake_cpu = val - stake_net;

   change_distribution_resource_limits( account, 0, stake_net, stake_cpu );
   
   control.get_mutable_voting_manager().update_voting_power(account, val);
}

void apply_context::reward_ram( const account_name& account, int64_t val )
{
   change_distribution_resource_limits( account, val, 0, 0 );
}

void apply_context::reward_all( uint64_t beos_to_distribute, uint64_t beos_to_distribute_trustee, uint64_t ram_to_distribute,
   uint64_t ram_to_distribute_trustee, const asset* proxyArray, size_t proxyArrayLen, block_producer_voting_info* start_producers, uint32_t* size )
{
   EOS_ASSERT( size != nullptr, transaction_exception, "size of producers must exist" );

   control.get_mutable_voting_manager().prepare_producers( start_producers, *size );

   reward_all( beos_to_distribute, beos_to_distribute_trustee, ram_to_distribute,
               ram_to_distribute_trustee, proxyArray, proxyArrayLen );

   *size = control.get_mutable_voting_manager().get_new_producers_size();
}

void apply_context::reward_all( uint64_t beos_to_distribute, uint64_t beos_to_distribute_trustee, uint64_t ram_to_distribute,
      uint64_t ram_to_distribute_trustee, const asset* proxyArray, size_t proxyArrayLen ) {
   const auto& accounts_index = db.template get_index<account_index, by_id>();

   // trustee is always rewarded with full given value
   if ( beos_to_distribute_trustee > 0 )
      reward_stake( N(beos.trustee), beos_to_distribute_trustee );
   if ( ram_to_distribute_trustee > 0 )
      reward_ram( N(beos.trustee), ram_to_distribute_trustee );

   uint64_t actual_beos_reward_sum = beos_to_distribute_trustee;
   uint64_t actual_ram_reward_sum = ram_to_distribute_trustee;
   BOOST_SCOPE_EXIT(this_,&actual_beos_reward_sum,&actual_ram_reward_sum) {
      // resources are interchangable so it doesn't matter that we are taking all from net (where beos.distrib stores resources to distribute)
      this_->change_resource_limits(config::distribution_account_name, -actual_ram_reward_sum, -actual_beos_reward_sum, 0 );
   } BOOST_SCOPE_EXIT_END;

   auto get_currency_balance = [this]( const symbol& asset_symbol, const table_id_object* tbl ) -> share_type {
      share_type result = 0;
      // the balance is implied to be 0 if either the table or row does not exist
      if (tbl) {
         const auto *obj = db.template find<key_value_object, by_scope_primary>(std::make_tuple(tbl->id, asset_symbol.to_symbol_code().value));
         if (obj) {
            //balance is the first field in the serialization
            fc::datastream<const char *> ds(obj->value.data(), obj->value.size());
            fc::raw::unpack(ds, result);
         }
      }
      return result;
   };

   if (proxyArrayLen == 0)
      return; // distributing only to beos.trustee since no proxy assets declared

   // prepare divisor from weighted amounts of active assets
   share_type divisor = 0;
   const auto* gateway_tbl = db.template find<table_id_object, by_code_scope_table>(std::make_tuple(N(eosio.token), config::gateway_account_name, N(accounts)));
   for (size_t i = 0; i < proxyArrayLen; ++i) {
      const asset& proxy = proxyArray[i];
      share_type issued = 0;
      const auto* tbl = db.template find<table_id_object, by_code_scope_table>(std::make_tuple(N(eosio.token), proxy.get_symbol().to_symbol_code().value, N(stat)));
      if (tbl) {
         const auto *obj = db.template find<key_value_object, by_scope_primary>(std::make_tuple(tbl->id, proxy.get_symbol().to_symbol_code().value));
         if (obj) {
            //supply is the first field in the serialization
            fc::datastream<const char *> ds(obj->value.data(), obj->value.size());
            fc::raw::unpack(ds, issued);
         }
      }
      share_type withdrawn = get_currency_balance(proxy.get_symbol(), gateway_tbl);
      issued -= withdrawn;
      if (issued > 0) {
        divisor += issued * proxy.get_amount();
      }
   }

   if ( divisor <= 0 )
      return; // nothing more to do here

   for (auto& account : accounts_index) {
      auto& name = account.name;
      if (name == config::gateway_account_name || name == config::distribution_account_name)
         continue; //neither beos.gateway (issuer of proxy) nor beos.distrib (source of rewards) can be rewarded
      auto& resource_limit_mgr = control.get_mutable_resource_limits_manager();
      int64_t current_ram_bytes = 0;
      int64_t current_net_weight = 0;
      int64_t current_cpu_weight = 0;
      resource_limit_mgr.get_account_limits( name, current_ram_bytes, current_net_weight, current_cpu_weight );

      const auto* user_tbl = db.template find<table_id_object, by_code_scope_table>(std::make_tuple(N(eosio.token), name, N(accounts)));
      int128_t balance = 0;
      // compute weighted balance for the account
      for (size_t i = 0; i < proxyArrayLen; ++i) {
         const asset& proxy = proxyArray[i];
         share_type proxy_balance = get_currency_balance(proxy.get_symbol(), user_tbl);
         balance += proxy_balance * proxy.get_amount();
      }
      if ( balance == 0 )
         continue; // not eligible for rewards
      if ( beos_to_distribute > 0 && current_net_weight >= 0 && current_cpu_weight >= 0 ) {
         // account that has unlimited bandwidth cannot be rewarded with bandwidth
         int128_t block_amount = balance * beos_to_distribute;
         long double dreward = static_cast<long double>(block_amount) / divisor;
         int64_t beos_reward = static_cast<int64_t>(dreward);
         if ( beos_reward > 0 ) {
            DBG("apply_context::reward_all: rewarding %s with beos %li",name.to_string().c_str(),beos_reward);
            actual_beos_reward_sum += beos_reward;
            reward_stake( name, beos_reward );
         }
      }
      if ( ram_to_distribute > 0 && current_ram_bytes >= 0 ) {
         // account that has unlimited ram cannot be rewarded with ram
         int128_t block_amount = balance * ram_to_distribute;
         long double dreward = static_cast<long double>(block_amount) / divisor;
         int64_t ram_reward = static_cast<int64_t>(dreward);
         if ( ram_reward > 0 ) {
            DBG("apply_context::reward_all: rewarding %s with ram %li",name.to_string().c_str(),ram_reward);
            actual_ram_reward_sum += ram_reward;
            reward_ram( name, ram_reward );
         }
      }
   }
}

void apply_context::reward_done()
{
   //TODO: stop producing distrib::onblock actions
}

void apply_context::exec( action_trace& trace )
{
   _notified.push_back(receiver);
   exec_one( trace );
   for( uint32_t i = 1; i < _notified.size(); ++i ) {
      receiver = _notified[i];
      trace.inline_traces.emplace_back( );
      exec_one( trace.inline_traces.back() );
   }

   if( _cfa_inline_actions.size() > 0 || _inline_actions.size() > 0 ) {
      EOS_ASSERT( recurse_depth < control.get_global_properties().configuration.max_inline_action_depth,
                  transaction_exception, "max inline action depth per transaction reached" );
   }

   for( const auto& inline_action : _cfa_inline_actions ) {
      trace.inline_traces.emplace_back();
      trx_context.dispatch_action( trace.inline_traces.back(), inline_action, inline_action.account, true, recurse_depth + 1 );
   }

   for( const auto& inline_action : _inline_actions ) {
      trace.inline_traces.emplace_back();
      trx_context.dispatch_action( trace.inline_traces.back(), inline_action, inline_action.account, false, recurse_depth + 1 );
   }

} /// exec()

bool apply_context::is_account( const account_name& account )const {
   return nullptr != db.find<account_object,by_name>( account );
}

void apply_context::require_authorization( const account_name& account ) {
   for( uint32_t i=0; i < act.authorization.size(); i++ ) {
     if( act.authorization[i].actor == account ) {
        used_authorizations[i] = true;
        return;
     }
   }
   EOS_ASSERT( false, missing_auth_exception, "missing authority of ${account}", ("account",account));
}

bool apply_context::has_authorization( const account_name& account )const {
   for( const auto& auth : act.authorization )
     if( auth.actor == account )
        return true;
  return false;
}

void apply_context::require_authorization(const account_name& account,
                                          const permission_name& permission) {
  for( uint32_t i=0; i < act.authorization.size(); i++ )
     if( act.authorization[i].actor == account ) {
        if( act.authorization[i].permission == permission ) {
           used_authorizations[i] = true;
           return;
        }
     }
  EOS_ASSERT( false, missing_auth_exception, "missing authority of ${account}/${permission}",
              ("account",account)("permission",permission) );
}

bool apply_context::has_recipient( account_name code )const {
   for( auto a : _notified )
      if( a == code )
         return true;
   return false;
}

void apply_context::require_recipient( account_name recipient ) {
   if( !has_recipient(recipient) ) {
      _notified.push_back(recipient);
   }
}


/**
 *  This will execute an action after checking the authorization. Inline transactions are
 *  implicitly authorized by the current receiver (running code). This method has significant
 *  security considerations and several options have been considered:
 *
 *  1. priviledged accounts (those marked as such by block producers) can authorize any action
 *  2. all other actions are only authorized by 'receiver' which means the following:
 *         a. the user must set permissions on their account to allow the 'receiver' to act on their behalf
 *
 *  Discarded Implemenation:  at one point we allowed any account that authorized the current transaction
 *   to implicitly authorize an inline transaction. This approach would allow privelege escalation and
 *   make it unsafe for users to interact with certain contracts.  We opted instead to have applications
 *   ask the user for permission to take certain actions rather than making it implicit. This way users
 *   can better understand the security risk.
 */
void apply_context::execute_inline( action&& a ) {
   auto* code = control.db().find<account_object, by_name>(a.account);
   EOS_ASSERT( code != nullptr, action_validate_exception,
               "inline action's code account ${account} does not exist", ("account", a.account) );

   for( const auto& auth : a.authorization ) {
      auto* actor = control.db().find<account_object, by_name>(auth.actor);
      EOS_ASSERT( actor != nullptr, action_validate_exception,
                  "inline action's authorizing actor ${account} does not exist", ("account", auth.actor) );
      EOS_ASSERT( control.get_authorization_manager().find_permission(auth) != nullptr, action_validate_exception,
                  "inline action's authorizations include a non-existent permission: ${permission}",
                  ("permission", auth) );
   }

   // No need to check authorization if: replaying irreversible blocks; contract is privileged; or, contract is calling itself.
   if( !control.skip_auth_check() && !privileged && a.account != receiver ) {
      control.get_authorization_manager()
             .check_authorization( {a},
                                   {},
                                   {{receiver, config::eosio_code_name}},
                                   control.pending_block_time() - trx_context.published,
                                   std::bind(&transaction_context::checktime, &this->trx_context),
                                   false
                                 );

      //QUESTION: Is it smart to allow a deferred transaction that has been delayed for some time to get away
      //          with sending an inline action that requires a delay even though the decision to send that inline
      //          action was made at the moment the deferred transaction was executed with potentially no forewarning?
   }

   _inline_actions.emplace_back( move(a) );
}

void apply_context::execute_context_free_inline( action&& a ) {
   auto* code = control.db().find<account_object, by_name>(a.account);
   EOS_ASSERT( code != nullptr, action_validate_exception,
               "inline action's code account ${account} does not exist", ("account", a.account) );

   EOS_ASSERT( a.authorization.size() == 0, action_validate_exception,
               "context-free actions cannot have authorizations" );

   _cfa_inline_actions.emplace_back( move(a) );
}


void apply_context::schedule_deferred_transaction( const uint128_t& sender_id, account_name payer, transaction&& trx, bool replace_existing ) {
   EOS_ASSERT( trx.context_free_actions.size() == 0, cfa_inside_generated_tx, "context free actions are not currently allowed in generated transactions" );
   trx.expiration = control.pending_block_time() + fc::microseconds(999'999); // Rounds up to nearest second (makes expiration check unnecessary)
   trx.set_reference_block(control.head_block_id()); // No TaPoS check necessary
   control.validate_referenced_accounts( trx );

   // Charge ahead of time for the additional net usage needed to retire the deferred transaction
   // whether that be by successfully executing, soft failure, hard failure, or expiration.
   const auto& cfg = control.get_global_properties().configuration;
   trx_context.add_net_usage( static_cast<uint64_t>(cfg.base_per_transaction_net_usage)
                               + static_cast<uint64_t>(config::transaction_id_net_usage) ); // Will exit early if net usage cannot be payed.

   auto delay = fc::seconds(trx.delay_sec);

   if( !control.skip_auth_check() && !privileged ) { // Do not need to check authorization if replayng irreversible block or if contract is privileged
      if( payer != receiver ) {
         require_authorization(payer); /// uses payer's storage
      }

      // if a contract is deferring only actions to itself then there is no need
      // to check permissions, it could have done everything anyway.
      bool check_auth = false;
      for( const auto& act : trx.actions ) {
         if( act.account != receiver ) {
            check_auth = true;
            break;
         }
      }
      if( check_auth ) {
         control.get_authorization_manager()
                .check_authorization( trx.actions,
                                      {},
                                      {{receiver, config::eosio_code_name}},
                                      delay,
                                      std::bind(&transaction_context::checktime, &this->trx_context),
                                      false
                                    );
      }
   }

   uint32_t trx_size = 0;
   if ( auto ptr = db.find<generated_transaction_object,by_sender_id>(boost::make_tuple(receiver, sender_id)) ) {
      EOS_ASSERT( replace_existing, deferred_tx_duplicate, "deferred transaction with the same sender_id and payer already exists" );

      // TODO: Remove the following subjective check when the deferred trx replacement RAM bug has been fixed with a hard fork.
      EOS_ASSERT( !control.is_producing_block(), subjective_block_production_exception,
                  "Replacing a deferred transaction is temporarily disabled." );

      // TODO: The logic of the next line needs to be incorporated into the next hard fork.
      // add_ram_usage( ptr->payer, -(config::billable_size_v<generated_transaction_object> + ptr->packed_trx.size()) );

      db.modify<generated_transaction_object>( *ptr, [&]( auto& gtx ) {
            gtx.sender      = receiver;
            gtx.sender_id   = sender_id;
            gtx.payer       = payer;
            gtx.published   = control.pending_block_time();
            gtx.delay_until = gtx.published + delay;
            gtx.expiration  = gtx.delay_until + fc::seconds(control.get_global_properties().configuration.deferred_trx_expiration_window);

            trx_size = gtx.set( trx );
         });
   } else {
      db.create<generated_transaction_object>( [&]( auto& gtx ) {
            gtx.trx_id      = trx.id();
            gtx.sender      = receiver;
            gtx.sender_id   = sender_id;
            gtx.payer       = payer;
            gtx.published   = control.pending_block_time();
            gtx.delay_until = gtx.published + delay;
            gtx.expiration  = gtx.delay_until + fc::seconds(control.get_global_properties().configuration.deferred_trx_expiration_window);

            trx_size = gtx.set( trx );
         });
   }

   EOS_ASSERT( control.is_ram_billing_in_notify_allowed() || (receiver == act.account) || (receiver == payer) || privileged,
               subjective_block_production_exception, "Cannot charge RAM to other accounts during notify." );
   add_ram_usage( payer, (config::billable_size_v<generated_transaction_object> + trx_size) );
}

bool apply_context::cancel_deferred_transaction( const uint128_t& sender_id, account_name sender ) {
   auto& generated_transaction_idx = db.get_mutable_index<generated_transaction_multi_index>();
   const auto* gto = db.find<generated_transaction_object,by_sender_id>(boost::make_tuple(sender, sender_id));
   if ( gto ) {
      add_ram_usage( gto->payer, -(config::billable_size_v<generated_transaction_object> + gto->packed_trx.size()) );
      generated_transaction_idx.remove(*gto);
   }
   return gto;
}

const table_id_object* apply_context::find_table( name code, name scope, name table ) {
   return db.find<table_id_object, by_code_scope_table>(boost::make_tuple(code, scope, table));
}

const table_id_object& apply_context::find_or_create_table( name code, name scope, name table, const account_name &payer ) {
   const auto* existing_tid =  db.find<table_id_object, by_code_scope_table>(boost::make_tuple(code, scope, table));
   if (existing_tid != nullptr) {
      return *existing_tid;
   }

   update_db_usage(payer, config::billable_size_v<table_id_object>);

   return db.create<table_id_object>([&](table_id_object &t_id){
      t_id.code = code;
      t_id.scope = scope;
      t_id.table = table;
      t_id.payer = payer;
   });
}

void apply_context::remove_table( const table_id_object& tid ) {
   update_db_usage(tid.payer, - config::billable_size_v<table_id_object>);
   db.remove(tid);
}

vector<account_name> apply_context::get_active_producers() const {
   const auto& ap = control.active_producers();
   vector<account_name> accounts; accounts.reserve( ap.producers.size() );

   for(const auto& producer : ap.producers )
      accounts.push_back(producer.producer_name);

   return accounts;
}

void apply_context::reset_console() {
   _pending_console_output = std::ostringstream();
   _pending_console_output.setf( std::ios::scientific, std::ios::floatfield );
}

bytes apply_context::get_packed_transaction() {
   auto r = fc::raw::pack( static_cast<const transaction&>(trx_context.trx) );
   return r;
}

void apply_context::update_db_usage( const account_name& payer, int64_t delta ) {
   if( delta > 0 ) {
      if( !(privileged || payer == account_name(receiver)) ) {
         EOS_ASSERT( control.is_ram_billing_in_notify_allowed() || (receiver == act.account),
                     subjective_block_production_exception, "Cannot charge RAM to other accounts during notify." );
         require_authorization( payer );
      }
   }
   add_ram_usage(payer, delta);
}


int apply_context::get_action( uint32_t type, uint32_t index, char* buffer, size_t buffer_size )const
{
   const auto& trx = trx_context.trx;
   const action* act_ptr = nullptr;

   if( type == 0 ) {
      if( index >= trx.context_free_actions.size() )
         return -1;
      act_ptr = &trx.context_free_actions[index];
   }
   else if( type == 1 ) {
      if( index >= trx.actions.size() )
         return -1;
      act_ptr = &trx.actions[index];
   }

   EOS_ASSERT(act_ptr, action_not_found_exception, "action is not found" );

   auto ps = fc::raw::pack_size( *act_ptr );
   if( ps <= buffer_size ) {
      fc::datastream<char*> ds(buffer, buffer_size);
      fc::raw::pack( ds, *act_ptr );
   }
   return ps;
}

int apply_context::get_context_free_data( uint32_t index, char* buffer, size_t buffer_size )const
{
   const auto& trx = trx_context.trx;

   if( index >= trx.context_free_data.size() ) return -1;

   auto s = trx.context_free_data[index].size();
   if( buffer_size == 0 ) return s;

   auto copy_size = std::min( buffer_size, s );
   memcpy( buffer, trx.context_free_data[index].data(), copy_size );

   return copy_size;
}

int apply_context::db_store_i64( uint64_t scope, uint64_t table, const account_name& payer, uint64_t id, const char* buffer, size_t buffer_size ) {
   return db_store_i64( receiver, scope, table, payer, id, buffer, buffer_size);
}

int apply_context::db_store_i64( uint64_t code, uint64_t scope, uint64_t table, const account_name& payer, uint64_t id, const char* buffer, size_t buffer_size ) {
//   require_write_lock( scope );
   const auto& tab = find_or_create_table( code, scope, table, payer );
   auto tableid = tab.id;

   EOS_ASSERT( payer != account_name(), invalid_table_payer, "must specify a valid account to pay for new record" );

   const auto& obj = db.create<key_value_object>( [&]( auto& o ) {
      o.t_id        = tableid;
      o.primary_key = id;
      o.value.resize( buffer_size );
      o.payer       = payer;
      memcpy( o.value.data(), buffer, buffer_size );
   });

   db.modify( tab, [&]( auto& t ) {
     ++t.count;
   });

   int64_t billable_size = (int64_t)(buffer_size + config::billable_size_v<key_value_object>);
   update_db_usage( payer, billable_size);

   keyval_cache.cache_table( tab );
   return keyval_cache.add( obj );
}

void apply_context::db_update_i64( int iterator, account_name payer, const char* buffer, size_t buffer_size ) {
   const key_value_object& obj = keyval_cache.get( iterator );

   const auto& table_obj = keyval_cache.get_table( obj.t_id );
   EOS_ASSERT( table_obj.code == receiver, table_access_violation, "db access violation" );

//   require_write_lock( table_obj.scope );

   const int64_t overhead = config::billable_size_v<key_value_object>;
   int64_t old_size = (int64_t)(obj.value.size() + overhead);
   int64_t new_size = (int64_t)(buffer_size + overhead);

   if( payer == account_name() ) payer = obj.payer;

   if( account_name(obj.payer) != payer ) {
      // refund the existing payer
      update_db_usage( obj.payer,  -(old_size) );
      // charge the new payer
      update_db_usage( payer,  (new_size));
   } else if(old_size != new_size) {
      // charge/refund the existing payer the difference
      update_db_usage( obj.payer, new_size - old_size);
   }

   db.modify( obj, [&]( auto& o ) {
     o.value.resize( buffer_size );
     memcpy( o.value.data(), buffer, buffer_size );
     o.payer = payer;
   });
}

void apply_context::db_remove_i64( int iterator ) {
   const key_value_object& obj = keyval_cache.get( iterator );

   const auto& table_obj = keyval_cache.get_table( obj.t_id );
   EOS_ASSERT( table_obj.code == receiver, table_access_violation, "db access violation" );

//   require_write_lock( table_obj.scope );

   update_db_usage( obj.payer,  -(obj.value.size() + config::billable_size_v<key_value_object>) );

   db.modify( table_obj, [&]( auto& t ) {
      --t.count;
   });
   db.remove( obj );

   if (table_obj.count == 0) {
      remove_table(table_obj);
   }

   keyval_cache.remove( iterator );
}

int apply_context::db_get_i64( int iterator, char* buffer, size_t buffer_size ) {
   const key_value_object& obj = keyval_cache.get( iterator );

   auto s = obj.value.size();
   if( buffer_size == 0 ) return s;

   auto copy_size = std::min( buffer_size, s );
   memcpy( buffer, obj.value.data(), copy_size );

   return copy_size;
}

int apply_context::db_next_i64( int iterator, uint64_t& primary ) {
   if( iterator < -1 ) return -1; // cannot increment past end iterator of table

   const auto& obj = keyval_cache.get( iterator ); // Check for iterator != -1 happens in this call
   const auto& idx = db.get_index<key_value_index, by_scope_primary>();

   auto itr = idx.iterator_to( obj );
   ++itr;

   if( itr == idx.end() || itr->t_id != obj.t_id ) return keyval_cache.get_end_iterator_by_table_id(obj.t_id);

   primary = itr->primary_key;
   return keyval_cache.add( *itr );
}

int apply_context::db_previous_i64( int iterator, uint64_t& primary ) {
   const auto& idx = db.get_index<key_value_index, by_scope_primary>();

   if( iterator < -1 ) // is end iterator
   {
      auto tab = keyval_cache.find_table_by_end_iterator(iterator);
      EOS_ASSERT( tab, invalid_table_iterator, "not a valid end iterator" );

      auto itr = idx.upper_bound(tab->id);
      if( idx.begin() == idx.end() || itr == idx.begin() ) return -1; // Empty table

      --itr;

      if( itr->t_id != tab->id ) return -1; // Empty table

      primary = itr->primary_key;
      return keyval_cache.add(*itr);
   }

   const auto& obj = keyval_cache.get(iterator); // Check for iterator != -1 happens in this call

   auto itr = idx.iterator_to(obj);
   if( itr == idx.begin() ) return -1; // cannot decrement past beginning iterator of table

   --itr;

   if( itr->t_id != obj.t_id ) return -1; // cannot decrement past beginning iterator of table

   primary = itr->primary_key;
   return keyval_cache.add(*itr);
}

int apply_context::db_find_i64( uint64_t code, uint64_t scope, uint64_t table, uint64_t id ) {
   //require_read_lock( code, scope ); // redundant?

   const auto* tab = find_table( code, scope, table );
   if( !tab ) return -1;

   auto table_end_itr = keyval_cache.cache_table( *tab );

   const key_value_object* obj = db.find<key_value_object, by_scope_primary>( boost::make_tuple( tab->id, id ) );
   if( !obj ) return table_end_itr;

   return keyval_cache.add( *obj );
}

int apply_context::db_lowerbound_i64( uint64_t code, uint64_t scope, uint64_t table, uint64_t id ) {
   //require_read_lock( code, scope ); // redundant?

   const auto* tab = find_table( code, scope, table );
   if( !tab ) return -1;

   auto table_end_itr = keyval_cache.cache_table( *tab );

   const auto& idx = db.get_index<key_value_index, by_scope_primary>();
   auto itr = idx.lower_bound( boost::make_tuple( tab->id, id ) );
   if( itr == idx.end() ) return table_end_itr;
   if( itr->t_id != tab->id ) return table_end_itr;

   return keyval_cache.add( *itr );
}

int apply_context::db_upperbound_i64( uint64_t code, uint64_t scope, uint64_t table, uint64_t id ) {
   //require_read_lock( code, scope ); // redundant?

   const auto* tab = find_table( code, scope, table );
   if( !tab ) return -1;

   auto table_end_itr = keyval_cache.cache_table( *tab );

   const auto& idx = db.get_index<key_value_index, by_scope_primary>();
   auto itr = idx.upper_bound( boost::make_tuple( tab->id, id ) );
   if( itr == idx.end() ) return table_end_itr;
   if( itr->t_id != tab->id ) return table_end_itr;

   return keyval_cache.add( *itr );
}

int apply_context::db_end_i64( uint64_t code, uint64_t scope, uint64_t table ) {
   //require_read_lock( code, scope ); // redundant?

   const auto* tab = find_table( code, scope, table );
   if( !tab ) return -1;

   return keyval_cache.cache_table( *tab );
}

uint64_t apply_context::next_global_sequence() {
   const auto& p = control.get_dynamic_global_properties();
   db.modify( p, [&]( auto& dgp ) {
      ++dgp.global_action_sequence;
   });
   return p.global_action_sequence;
}

uint64_t apply_context::next_recv_sequence( account_name receiver ) {
   const auto& rs = db.get<account_sequence_object,by_name>( receiver );
   db.modify( rs, [&]( auto& mrs ) {
      ++mrs.recv_sequence;
   });
   return rs.recv_sequence;
}
uint64_t apply_context::next_auth_sequence( account_name actor ) {
   const auto& rs = db.get<account_sequence_object,by_name>( actor );
   db.modify( rs, [&](auto& mrs ){
      ++mrs.auth_sequence;
   });
   return rs.auth_sequence;
}

void apply_context::add_ram_usage( account_name account, int64_t ram_delta ) {
   trx_context.add_ram_usage( account, ram_delta );

   auto p = _account_ram_deltas.emplace( account, ram_delta );
   if( !p.second ) {
      p.first->delta += ram_delta;
   }
}


} } /// eosio::chain
