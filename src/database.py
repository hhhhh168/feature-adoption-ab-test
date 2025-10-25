"""
Database management utilities for A/B Testing Platform
Handles Supabase PostgreSQL connections and operations
"""
import pandas as pd
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
import logging
from src.config import DB_CONFIG, DatabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage Supabase database connections and operations"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database manager

        Args:
            config: Database configuration (defaults to global DB_CONFIG)
        """
        self.config = config or DB_CONFIG

        if not self.config.is_configured():
            logger.warning("Database not configured. Set SUPABASE_URL and SUPABASE_KEY.")
            self.client = None
        else:
            try:
                self.client: Client = create_client(
                    self.config.url,
                    self.config.key
                )
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                self.client = None

    def is_connected(self) -> bool:
        """Check if database connection is active"""
        return self.client is not None

    def execute_sql(self, sql: str) -> Any:
        """
        Execute raw SQL query

        Args:
            sql: SQL query string

        Returns:
            Query result
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        try:
            result = self.client.postgrest.rpc('execute_sql', {'query': sql}).execute()
            return result
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise

    def execute_sql_file(self, filepath: str):
        """
        Execute SQL file for schema creation

        Args:
            filepath: Path to SQL file
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        logger.info(f"Executing SQL file: {filepath}")

        with open(filepath, 'r') as f:
            sql = f.read()

        # Split and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for i, stmt in enumerate(statements):
            try:
                self.execute_sql(stmt)
                logger.debug(f"Statement {i+1}/{len(statements)} executed")
            except Exception as e:
                logger.error(f"Failed to execute statement {i+1}: {e}")
                logger.debug(f"Statement: {stmt[:100]}...")
                raise

        logger.info(f"Successfully executed {len(statements)} statements")

    def insert_dataframe(self, table_name: str, df: pd.DataFrame, batch_size: int = 1000):
        """
        Insert pandas DataFrame into table in batches

        Args:
            table_name: Target table name
            df: DataFrame to insert
            batch_size: Number of records per batch
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        logger.info(f"Inserting {len(df)} records into {table_name}")

        # Convert DataFrame to list of dicts
        records = df.to_dict('records')

        # Insert in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                self.client.table(table_name).insert(batch).execute()
                logger.debug(f"Inserted batch {i//batch_size + 1}/{(len(records)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Failed to insert batch: {e}")
                raise

        logger.info(f"Successfully inserted {len(records)} records")

    def query(self, query: str) -> pd.DataFrame:
        """
        Execute query and return DataFrame

        Args:
            query: SQL query string

        Returns:
            Query results as DataFrame
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        try:
            result = self.execute_sql(query)
            if hasattr(result, 'data'):
                return pd.DataFrame(result.data)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def query_table(self, table_name: str,
                    select: str = '*',
                    filters: Optional[Dict[str, Any]] = None,
                    limit: Optional[int] = None) -> pd.DataFrame:
        """
        Query table using Supabase query builder

        Args:
            table_name: Table to query
            select: Columns to select
            filters: Dict of column: value filters
            limit: Maximum rows to return

        Returns:
            Query results as DataFrame
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        query = self.client.table(table_name).select(select)

        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)

        if limit:
            query = query.limit(limit)

        try:
            result = query.execute()
            return pd.DataFrame(result.data)
        except Exception as e:
            logger.error(f"Table query failed: {e}")
            raise

    def get_experiment_data(self,
                           experiment_id: str,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch all experiment-related data

        Args:
            experiment_id: Experiment identifier
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)

        Returns:
            Dictionary of DataFrames with experiment data
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        logger.info(f"Fetching data for experiment: {experiment_id}")

        # Build date filter
        date_filter = ""
        if start_date and end_date:
            date_filter = f"AND event_timestamp BETWEEN '{start_date}' AND '{end_date}'"

        queries = {
            'users': f"""
                SELECT u.*, a.variant
                FROM users u
                JOIN experiment_assignments a ON u.user_id = a.user_id
                WHERE a.experiment_id = '{experiment_id}'
            """,
            'pre_metrics': f"""
                SELECT pm.*, a.variant
                FROM user_pre_metrics pm
                JOIN experiment_assignments a ON pm.user_id = a.user_id
                WHERE a.experiment_id = '{experiment_id}'
            """,
            'assignments': f"""
                SELECT * FROM experiment_assignments
                WHERE experiment_id = '{experiment_id}'
            """,
            'events': f"""
                SELECT * FROM events
                WHERE experiment_id = '{experiment_id}' {date_filter}
            """,
            'verification': f"""
                SELECT * FROM verification_attempts
                WHERE experiment_id = '{experiment_id}' {date_filter}
            """,
            'engagement': f"""
                SELECT * FROM user_engagement_metrics
                WHERE experiment_id = '{experiment_id}'
            """,
            'funnel': f"""
                SELECT * FROM verification_funnel_metrics
                WHERE experiment_id = '{experiment_id}'
            """
        }

        data = {}
        for key, query in queries.items():
            try:
                data[key] = self.query(query)
                logger.info(f"  Loaded {key}: {len(data[key])} records")
            except Exception as e:
                logger.warning(f"  Failed to load {key}: {e}")
                data[key] = pd.DataFrame()

        return data

    def refresh_materialized_view(self, view_name: str, concurrent: bool = False):
        """
        Refresh materialized view

        Args:
            view_name: Name of materialized view
            concurrent: Use CONCURRENTLY for non-blocking refresh
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        concurrent_str = "CONCURRENTLY" if concurrent else ""
        sql = f"REFRESH MATERIALIZED VIEW {concurrent_str} {view_name}"

        logger.info(f"Refreshing materialized view: {view_name}")
        self.execute_sql(sql)
        logger.info(f"Successfully refreshed {view_name}")

    def refresh_all_views(self, concurrent: bool = False):
        """Refresh all materialized views"""
        views = [
            'user_engagement_metrics',
            'daily_experiment_metrics',
            'verification_funnel_metrics'
        ]

        for view in views:
            try:
                self.refresh_materialized_view(view, concurrent)
            except Exception as e:
                logger.error(f"Failed to refresh {view}: {e}")

    def truncate_table(self, table_name: str, cascade: bool = False):
        """
        Truncate table (delete all data)

        Args:
            table_name: Table to truncate
            cascade: Use CASCADE option

        WARNING: This deletes all data!
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        cascade_str = "CASCADE" if cascade else ""
        sql = f"TRUNCATE TABLE {table_name} {cascade_str}"

        logger.warning(f"Truncating table: {table_name}")
        self.execute_sql(sql)
        logger.info(f"Successfully truncated {table_name}")

    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """
        Get basic statistics about a table

        Args:
            table_name: Table to analyze

        Returns:
            Dictionary with table statistics
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        count_df = self.query(count_query)

        return {
            'table_name': table_name,
            'row_count': int(count_df['count'].iloc[0]) if not count_df.empty else 0
        }

    def validate_schema(self) -> Dict[str, bool]:
        """
        Validate that all required tables exist

        Returns:
            Dictionary of table_name: exists
        """
        if not self.is_connected():
            raise ConnectionError("Database not connected")

        required_tables = [
            'users',
            'user_pre_metrics',
            'experiments',
            'experiment_assignments',
            'events',
            'verification_attempts',
            'verification_status'
        ]

        results = {}
        for table in required_tables:
            try:
                query = f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = '{table}'
                    )
                """
                result = self.query(query)
                results[table] = result.iloc[0, 0] if not result.empty else False
            except Exception as e:
                logger.error(f"Failed to check {table}: {e}")
                results[table] = False

        return results


def create_database_schema(db_manager: DatabaseManager, schema_file: str):
    """
    Helper function to create database schema from SQL file

    Args:
        db_manager: DatabaseManager instance
        schema_file: Path to schema SQL file
    """
    logger.info("Creating database schema...")
    db_manager.execute_sql_file(schema_file)
    logger.info("Database schema created successfully")


def create_materialized_views(db_manager: DatabaseManager, views_file: str):
    """
    Helper function to create materialized views from SQL file

    Args:
        db_manager: DatabaseManager instance
        views_file: Path to materialized views SQL file
    """
    logger.info("Creating materialized views...")
    db_manager.execute_sql_file(views_file)
    logger.info("Materialized views created successfully")


if __name__ == "__main__":
    # Test database connection
    db = DatabaseManager()

    if db.is_connected():
        print("✅ Database connected successfully")
        print("\nValidating schema...")
        schema_status = db.validate_schema()
        for table, exists in schema_status.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {table}")
    else:
        print("❌ Database not connected")
        print("Set SUPABASE_URL and SUPABASE_KEY environment variables")
