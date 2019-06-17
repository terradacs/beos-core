#include <eosio/jurisdiction_history_plugin/jurisdiction_history_plugin.hpp>

namespace eosio
{
  static appbase::abstract_plugin& _jurisdiction_history_plugin = app().register_plugin<jurisdiction_history_plugin>();

  class jurisdiction_history_plugin_impl
  {
    public:
      chain_plugin *chain_plug = nullptr;
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
    ilog("initializing jurisdiction_history_plugin");
    try 
    {
      my->chain_plug = app().find_plugin<chain_plugin>();
      EOS_ASSERT(my->chain_plug, chain::missing_chain_plugin_exception, "");
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
        const auto &idx_by_producer_block = db.db().get_index<chain::jurisdiction_history_index, chain::by_producer_block_number>();
        auto search = idx_by_producer_block.lower_bound(boost::make_tuple(params.producer,
                                                         params.block_number.valid() ? *params.block_number : db.head_block_num() ));
        if (search->block_number == params.block_number && search->producer_name == params.producer)
        {
          result.producer_jurisdiction_for_block.emplace_back(jurisdiction_history_api_object(*search));
        }
        else
        {
          if (search != idx_by_producer_block.begin())
          {
            --search;
            if (search->producer_name == params.producer)
            {
              result.producer_jurisdiction_for_block.emplace_back(jurisdiction_history_api_object(*search));
            }
          }
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
      EOS_ASSERT(params.limit <= JURISDICTION_HISTORY_QUERY_LIMIT, fc::invalid_arg_exception, "Invalid value for limit ${s} > ${n}", ("s", params.limit)("n", JURISDICTION_HISTORY_QUERY_LIMIT));
      read_write::get_producer_jurisdiction_history_results result;
      try 
      {
        const auto &idx_by_date_changed = db.db().get_index<chain::jurisdiction_history_index, chain::by_date_changed>();
        const fc::time_point from_date = params.from_date.valid() ? *params.from_date : fc::time_point();
        const fc::time_point to_date = params.to_date.valid() ? *params.to_date : fc::time_point::now();

        auto itr = idx_by_date_changed.lower_bound(from_date);
        uint16_t count = 0;
        while (itr != idx_by_date_changed.end() && itr->date_changed < to_date && count < params.limit)
        {
          if (itr->producer_name == params.producer)
          {
            result.producer_jurisdiction_history.emplace_back(jurisdiction_history_api_object(*itr));
            ++count;
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
