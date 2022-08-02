// Description:
//   A more helpful help command.
//
// Dependencies:
//   "stopwords": "0.0.5"
//
// Configuration:
//   HUBOT_HELP_NO_GREETINGS=true - tells hubot to not listen for mentions such as 'ask hubot' or 'hi hubot'
//
// Commands:
//   hubot help - The friendly help prompt
//
// Notes:
//   This module is written with typescript, and all javascript files are generated.  If you want to make changes
//   please clone the source from https://github.com/CruAlbania/hubot-better-help
//
// Author:
//   gburgett
Object.defineProperty(exports, "__esModule", { value: true });
const index_1 = require("./better-help/index");
const parser_1 = require("./better-help/parser");
const search_1 = require("./better-help/search");
module.exports = (robot) => {
    const cwd = '.';
    // --------------- Greetings ------------------------------------ //
    if (!process.env.HUBOT_HELP_NO_GREETINGS) {
        require('./better-help/greetings')(robot);
    }
    // load dependencies and then respond with help
    const parser = new parser_1.HelpParser(robot.logger, cwd);
    parser.parseScripts()
        .then((scripts) => {
        search_1.Searcher.LoadSearchIndex(scripts)
            .then((searcher) => {
            // Respond with help from hubot scripts
            index_1.InitHelp(robot, scripts, searcher);
        })
            .catch((error) => {
            robot.logger.error('Unable to create search index:', error);
        });
    })
        .catch((error) => {
        robot.logger.error('Unable to load help scripts:', error);
    });
};
