#pragma once

#include <stdint.h>

struct block_producer_voting_info
   {
   uint64_t owner_account_name = 0;
   double   total_votes = 0;
   bool     is_active = false;
   };
