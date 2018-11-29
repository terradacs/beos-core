#pragma once

#ifdef __cplusplus
extern "C" {
#endif

   struct block_producer_voting_info;

   /**
    * @defgroup privilegedapi Privileged API
    * @ingroup systemapi
    * @brief Defines an API for accessing configuration of the chain that can only be done by privileged accounts
    */

   /**
    * @defgroup privilegedcapi Privileged C API
    * @ingroup privilegedapi
    * @brief Defines %C Privileged API
    *
    * @{
    */

  /**
    * @brief Get the resource rewards of an account gathered during a distribution period
    * Get the resource rewards of an account
    * @param account - name of the account whose resource limit to get
    * @param ram_bytes - pointer to `int64_t` to hold ram rewards in absolute bytes
    * @param net_weight - pointer to `int64_t` to hold net rewards
    * @param cpu_weight - pointer to `int64_t` to hold cpu rewards
    */
   void get_distribution_resource_rewards( account_name account, int64_t* ram_bytes, int64_t* net_weight, int64_t* cpu_weight );

  /**
    * @brief Get the resource limits of an account
    * Get the resource limits of an account
    * @param account - name of the account whose resource limit to get
    * @param ram_bytes - pointer to `int64_t` to hold retrieved ram limit in absolute bytes
    * @param net_weight - pointer to `int64_t` to hold net limit
    * @param cpu_weight - pointer to `int64_t` to hold cpu limit
    */
   void get_resource_limits( account_name account, int64_t* ram_bytes, int64_t* net_weight, int64_t* cpu_weight );

   /**
    * @brief Set the resource limits of an account
    * Set the resource limits of an account
    * @param account - name of the account whose resource limit to be set
    * @param ram_bytes - ram limit in absolute bytes
    * @param net_weight - fractionally proportionate net limit of available resources based on (weight / total_weight_of_all_accounts)
    * @param cpu_weight - fractionally proportionate cpu limit of available resources based on (weight / total_weight_of_all_accounts)
    */
   void set_resource_limits( account_name account, int64_t ram_bytes, int64_t net_weight, int64_t cpu_weight );

   /**
    * @brief Retrieves the current ram usage for an account
    * @param account - name of the account
    */
   int64_t get_account_ram_usage( account_name account );

   /**
    * @brief Change the resource limits of an account
    * Change the resource limits of an account - cannot be called with nonzero value on unlimited resource
    * @param account - name of the account whose resource limit to be changed
    * @param ram_bytes - ram delta limit in absolute bytes
    * @param net_weight - fractionally proportionate net delta limit of available resources based on (weight / total_weight_of_all_accounts)
    * @param cpu_weight - fractionally proportionate cpu delta limit of available resources based on (weight / total_weight_of_all_accounts)
    */
   void change_resource_limits( account_name account, int64_t ram_bytes, int64_t net_weight, int64_t cpu_weight );

   /**
    * Proposes a schedule change, once the block that contains the proposal becomes irreversible, the schedule is promoted to "pending" automatically. Once the block that promotes the schedule is irreversible, the schedule will become "active"
    * @param producer_data - packed data of produce_keys in the appropriate producer schedule order
    * @param producer_data_size - size of the data buffer
    *
    * @return -1 if proposing a new producer schedule was unsuccessful, otherwise returns the version of the new proposed schedule
    */
   int64_t set_proposed_producers( char *producer_data, uint32_t producer_data_size );

   /**
    * @brief Set new active producers
    * Set new active producers. Producers will only be activated once the block which starts the next round is irrreversible
    * @param producer_data - pointer to producer schedule packed as bytes
    * @param producer_data_size - size of the packed producer schedule
    * @pre `producer_data` is a valid pointer to a range of memory at least `producer_data_size` bytes long that contains serialized produced schedule data
    */
   void set_active_producers( char *producer_data, uint32_t producer_data_size );
   /**
    * @brief Check if an account is privileged
    * Check if an account is privileged
    * @param account - name of the account to be checked
    * @return true if the account is privileged
    * @return false if the account is not privileged
    */
   bool is_privileged( account_name account );

   /**
    * @brief Set the privileged status of an account
    * Set the privileged status of an account
    * @param account - name of the account whose privileged account to be set
    * @param is_priv - privileged status
    */
   void set_privileged( account_name account, bool is_priv );

   /**
    * @brief Set the blockchain parameters
    * Set the blockchain parameters
    * @param data - pointer to blockchain parameters packed as bytes
    * @param datalen - size of the packed blockchain parameters
    * @pre `data` is a valid pointer to a range of memory at least `datalen` bytes long that contains packed blockchain params data
    */
   void set_blockchain_parameters_packed(char* data, uint32_t datalen);

   /**
    * @brief Retrieve the blolckchain parameters
    * Retrieve the blolckchain parameters
    * @param data - output buffer of the blockchain parameters, only retrieved if sufficent size to hold packed data.
    * @param datalen - size of the data buffer, 0 to report required size.
    * @return size of the blockchain parameters
    * @pre `data` is a valid pointer to a range of memory at least `datalen` bytes long
    * @post `data` is filled with packed blockchain parameters
    */
   uint32_t get_blockchain_parameters_packed(char* data, uint32_t datalen);

   /**
    * @brief Activate new feature
    * Activate new feature
    * @param f - name (identifier) of the feature to be activated
    */
   void activate_feature( int64_t f );

   void get_voting_stats(int64_t* total_activated_stake, uint64_t* thresh_activated_stake_time,
      double* total_producer_vote_weight);

   void store_voting_stats(int64_t total_activated_stake, uint64_t thresh_activated_stake_time,
      double total_producer_vote_weight);

   void set_min_activated_stake(int64_t);

   int64_t get_min_activated_stake();

   /** @brief Registers given account as a proxy (if is_proxy is true)
       Part of system_contract implementation (regproxy action).
   */
   void register_voting_proxy(const account_name proxy, bool is_proxy,
      block_producer_voting_info* producerInfos, uint32_t producerInfoSize);

   /** @brief Updates the voting power of given account after changing its amount of stake.
       Part of system_contract implementation (changebw function).
   */
   void update_voting_power(const account_name voter, int64_t stake_delta,
      block_producer_voting_info* producerInfos, uint32_t producerInfoSize);

   /** @brief Allows to update votes.
       Part of system_contract implementation.
   */
   void update_votes(const account_name voter_name, const account_name proxy, const account_name* producers,
      uint32_t producer_size, bool voting,
      block_producer_voting_info* producerInfos, uint32_t producerInfoSize);

   ///@ } privilegedcapi
#ifdef __cplusplus
}
#endif
