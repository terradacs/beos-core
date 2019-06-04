#include <eosio/jurisdiction_history_plugin/jurisdiction_history_plugin.hpp>
#include <boost/signals2/connection.hpp>

namespace eosio
{
  static appbase::abstract_plugin& _jurisdiction_history_plugin = app().register_plugin<jurisdiction_history_plugin>();

  class jurisdiction_history_plugin_impl
  {
    public:
      struct updateprod
      {
        chain::account_name producer;
        std::vector<chain::code_jurisdiction> new_jurisdictions;
      };

      chain_plugin *chain_plug = nullptr;
      fc::optional<boost::signals2::scoped_connection> applied_transaction_connection;

      void on_applied_transaction(const chain::transaction_trace_ptr& trace)
      {
        for(const auto &atrace : trace->action_traces) 
        {
          if (atrace.act.name == N(updateprod))
          {
            ilog("=== updateprod detected by account ${n}", ("n", atrace.act.account));
            ilog("    block num ${n}", ("n", trace->block_num));
            //on_producer_jurisdiction_change(atrace.act.account, trace->block_num, trace->block_time, act_data.new_jurisdictions);
          }
        }
      }

      void on_producer_jurisdiction_change(const chain::account_name &producer, uint64_t block_number, fc::time_point date_changed, std::vector<chain::code_jurisdiction> &new_jurisdictions)
      {
        if (chain_plug != nullptr)
        {
          chainbase::database& rw_db = const_cast<chainbase::database&>(chain_plug->chain().db()); // Override read-only access to state DB (highly unrecommended practice!)
          rw_db.create<jurisdiction_history_object>([&](jurisdiction_history_object &ob){
            ob.producer_name = producer;
            ob.block_number = block_number;
            ob.date_changed = date_changed;
            ob.new_jurisdictions = new_jurisdictions;
          });
        }
      }
  };

  jurisdiction_history_plugin::jurisdiction_history_plugin() : my(new jurisdiction_history_plugin_impl())
  {

  }
  
  jurisdiction_history_plugin::~jurisdiction_history_plugin()
  {

  }

  void jurisdiction_history_plugin::set_program_options(options_description& cli, options_description& cfg)
  {

  }

  void jurisdiction_history_plugin::plugin_initialize(const variables_map& options)
  {
    try 
    {
      my->chain_plug = app().find_plugin<chain_plugin>();
      EOS_ASSERT(my->chain_plug, chain::missing_chain_plugin_exception, "");
      auto& chain = my->chain_plug->chain();

      chainbase::database& db = const_cast<chainbase::database&>(chain.db()); // Override read-only access to state DB (highly unrecommended practice!)
      db.add_index<jurisdiction_history_multi_index>();
      
      my->applied_transaction_connection.emplace(
        chain.applied_transaction.connect([&](const chain::transaction_trace_ptr& p){
          my->on_applied_transaction(p);
        })
      );
    }
    FC_LOG_AND_RETHROW()
  }

  void jurisdiction_history_plugin::plugin_startup()
  {

  }

  void jurisdiction_history_plugin::plugin_shutdown() 
  {

  }

  jurisdiction_history_apis::read_write jurisdiction_history_plugin::get_read_write_api() const
  {
    controller& c = my->chain_plug->chain();
    return jurisdiction_history_apis::read_write(c, my->chain_plug->get_abi_serializer_max_time());
  }

  namespace jurisdiction_history_apis
  {
    read_write::get_producer_jurisdiction_for_block_results read_write::get_producer_jurisdiction_for_block(const read_write::get_producer_jurisdiction_for_block_params &params)
    {
      read_write::get_producer_jurisdiction_for_block_results result;
      try 
      {
        const auto &idx_by_producer_block = db.db().get_index<jurisdiction_history_multi_index, by_producer_block_number>();
        auto search = idx_by_producer_block.find(boost::make_tuple(params.producer, params.block_number));
        if (search != idx_by_producer_block.end())
        {
          result.producer_jurisdiction_for_block = jurisdiction_history_api_object(*search);
        }
      }
      catch (const fc::exception& e) 
      {
        throw e;
      }
      catch( const std::exception& e ) 
      {
        auto fce = fc::exception(
          FC_LOG_MESSAGE( info, "Caught std::exception: ${what}", ("what",e.what())),
          fc::std_exception_code,
          BOOST_CORE_TYPEID(e).name(),
          e.what()
        );
        throw fce;
      }
      catch( ... ) 
      {
        auto fce = fc::unhandled_exception(
          FC_LOG_MESSAGE( info, "Caught unknown exception"),
          std::current_exception()
        );
        throw fce;
      }
      return result;
    }

    read_write::get_producer_jurisdiction_history_results read_write::get_producer_jurisdiction_history(const read_write::get_producer_jurisdiction_history_params &params)
    {
      read_write::get_producer_jurisdiction_history_results result;
      try 
      {
        const auto &idx_by_date_changed = db.db().get_index<jurisdiction_history_multi_index, by_date_changed>();
        auto itr = idx_by_date_changed.lower_bound(params.from_date);
        while (itr != idx_by_date_changed.end() && itr->date_changed < params.to_date)
        {
          if (itr->producer_name == params.producer)
          {
            result.producer_jurisdiction_history.emplace_back(jurisdiction_history_api_object(*itr));
          }
          ++itr;
        }
      } 
      catch (const fc::exception& e) 
      {
        throw e;
      }
      catch( const std::exception& e ) 
      {
        auto fce = fc::exception(
          FC_LOG_MESSAGE( info, "Caught std::exception: ${what}", ("what",e.what())),
          fc::std_exception_code,
          BOOST_CORE_TYPEID(e).name(),
          e.what()
        );
        throw fce;
      }
      catch( ... ) 
      {
        auto fce = fc::unhandled_exception(
          FC_LOG_MESSAGE( info, "Caught unknown exception"),
          std::current_exception()
        );
        throw fce;
      }
      return result;
    }
  } // namespace jurisdiction_history_apis
}