// Ported from dsh-gomoku game.ts (MIT); host HTTP request and TS types omitted.
export const BOARD_SIZE=15,EMPTY=0,BLACK=1,WHITE=2,CELL_COUNT=225;
export function isLegalMove(board,row,col){return row>=0&&row<BOARD_SIZE&&col>=0&&col<BOARD_SIZE&&board[row*BOARD_SIZE+col]===EMPTY;}
export function hasEmpty(board){return board.includes(EMPTY);}
const DIRECTIONS=[[0,1],[1,0],[1,1],[1,-1]];
export function winsAt(board,row,col){
 const color=board[row*BOARD_SIZE+col];if(color===EMPTY)return false;
 for(const[dr,dc]of DIRECTIONS){let count=1;for(const step of[1,-1]){let r=row+dr*step,c=col+dc*step;while(r>=0&&r<BOARD_SIZE&&c>=0&&c<BOARD_SIZE&&board[r*BOARD_SIZE+c]===color){count++;r+=dr*step;c+=dc*step;}}if(count>=5)return true;}return false;
}
