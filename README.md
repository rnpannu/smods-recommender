<h1>Smods-recommender</h1>
A system to recommend developers for the Steamodded ([SMODS](https://github.com/Steamodded/smods)) project according to their modification history. Mines commits and creates a map of function-level expertise for each developer. 
Query using function names and customizable weights for modificiation expertise, call expertise, diversity/breadth of functions addressed, consistency of contributions over time, and a half-life time decay.
  
<h3>How to use</h3>
  1. Build expertise map by running the parse_logs script.
  <br/>
  2. Query the recommender by passing in function names as argument to the recommend_devs script. Including --simple strips the scoring function to basic frequency counts and a linear time decay. Complex scoring also has optional parameters mod_weight, call_weight, decay_window, diversity_weight, consistency_weight.
<br><br/>
<br><br/>
<b>Example</b> (Issue fixer - Aurelius):
<br><br/>
<img width="1385" height="493" alt="complex" src="https://github.com/user-attachments/assets/75308e5f-fa14-4775-8778-21cd90361ec8" />
<br/>
<div align="center">Complex scoring</div>
<br/>
<img width="1513" height="479" alt="simple" src="https://github.com/user-attachments/assets/7cf9f767-2a02-42a9-a890-b36eac36c24d" />
<br/>
<div align="center">Simple scoring</div>
<br/>
<br/>
The system uses the Treesitter Neovim API to obtain function definitions from the syntax tree.
<br/>
<img width="1920" height="626" alt="r(2)" src="https://github.com/user-attachments/assets/d723c6eb-a0e8-4574-9734-ec7e2f84db7d" />

