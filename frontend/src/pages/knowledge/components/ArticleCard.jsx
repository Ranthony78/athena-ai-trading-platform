import { Badge } from "../../../components/common";
import { truncate } from "../../../utils/helpers";

export default function ArticleCard({ article }) {
    return (
        <a href={`/knowledge/articles/${article.slug}`}>
            <div className="card hover:border-dark-600 cursor-pointer
                      transition-colors h-full">
                <div className="flex items-start justify-between mb-2">
                    <Badge variant="blue">{article.category}</Badge>
                    {article.is_featured && (
                        <span className="text-xs text-yellow-400">⭐</span>
                    )}
                </div>
                <h3 className="text-sm font-semibold text-dark-100 mb-2">
                    {article.title}
                </h3>
                {article.summary && (
                    <p className="text-xs text-dark-400">
                        {truncate(article.summary, 120)}
                    </p>
                )}
            </div>
        </a>
    );
}